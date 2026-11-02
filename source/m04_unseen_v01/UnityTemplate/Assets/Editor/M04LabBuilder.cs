using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using TMPro;
using ModStudioM04;

[Serializable]
internal sealed class M04SpecRow
{
    public string case_id;
    public string kind;
    public string text;
    public string template;
    public string key;
    public string resource_name;
    public int kind_index;
    public int arg0;
    public int arg1;
}

[Serializable]
internal sealed class M04Spec
{
    public string eval_id;
    public M04SpecRow[] rows;
}

public static class M04LabBuilder
{
    private const string ScenePath = "Assets/M04/Scenes/UnseenLabB.unity";
    private const string TablePath = "Assets/M04/Data/M04HoldoutTable.asset";

    private static string ProjectRoot
    {
        get { return Directory.GetParent(Application.dataPath).FullName; }
    }

    private static M04Spec LoadSpec()
    {
        var path = Path.Combine(ProjectRoot, "ProjectSettings", "M04HoldoutLocal.json");
        if (!File.Exists(path)) throw new InvalidOperationException("Missing PRIVATE local spec: " + path);
        var spec = JsonUtility.FromJson<M04Spec>(File.ReadAllText(path));
        if (spec == null || spec.rows == null || spec.rows.Length != 20)
            throw new InvalidOperationException("M04 spec must contain exactly 20 records.");
        return spec;
    }

    private static void EnsureFolder(string assetFolder)
    {
        string[] parts = assetFolder.Split('/');
        string parent = parts[0];
        for (int i = 1; i < parts.Length; ++i)
        {
            string next = parent + "/" + parts[i];
            if (!AssetDatabase.IsValidFolder(next)) AssetDatabase.CreateFolder(parent, parts[i]);
            parent = next;
        }
    }

    private static TextMeshProUGUI MakeLabel(string name, string initial, int y)
    {
        var go = new GameObject(name, typeof(RectTransform), typeof(CanvasRenderer));
        var label = go.AddComponent<TextMeshProUGUI>();
        label.font = TMP_Settings.defaultFontAsset;
        label.fontSize = 21;
        label.color = Color.white;
        label.alignment = TextAlignmentOptions.Left;
        label.enableWordWrapping = false;
        label.text = initial;
        var rt = (RectTransform)go.transform;
        rt.anchorMin = rt.anchorMax = new Vector2(0, 1);
        rt.pivot = new Vector2(0, 1);
        rt.anchoredPosition = new Vector2(24, -16 - y * 47);
        rt.sizeDelta = new Vector2(1550, 44);
        return label;
    }

    [MenuItem("Tools/Mod Studio AI/M04/Generate Unseen Lab B Scene")]
    public static void GenerateScene()
    {
        if (TMP_Settings.defaultFontAsset == null)
            throw new InvalidOperationException("Import TextMeshPro Essential Resources first.");
        if (AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath) != null)
            throw new InvalidOperationException("Scene already exists; M04 is immutable. Create a NEW lab project/seed to regenerate.");
        var spec = LoadSpec();
        if (spec.rows.Count(x => x.kind == "prefab") != 3 ||
            spec.rows.Count(x => x.kind == "table") != 3 ||
            spec.rows.Count(x => x.kind == "hardcoded") != 3 ||
            spec.rows.Count(x => x.kind == "runtime") != 3 ||
            spec.rows.Count(x => x.kind == "json") != 3 ||
            spec.rows.Count(x => x.kind.StartsWith("negative_", StringComparison.Ordinal)) != 5)
            throw new InvalidOperationException("Invalid M04 kind distribution.");

        EnsureFolder("Assets/M04/Scenes");
        EnsureFolder("Assets/M04/Data");
        EnsureFolder("Assets/M04/Prefabs");
        EnsureFolder("Assets/Resources");
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var cam = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener));
        cam.tag = "MainCamera";
        cam.GetComponent<Camera>().clearFlags = CameraClearFlags.SolidColor;
        cam.GetComponent<Camera>().backgroundColor = new Color(0.08f, 0.10f, 0.14f);

        var canvasObj = new GameObject("M04_Canvas", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
        var canvas = canvasObj.GetComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        var scaler = canvasObj.GetComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1600, 960);

        var positives = spec.rows.Where(x => !x.kind.StartsWith("negative_", StringComparison.Ordinal)).ToArray();
        var table = ScriptableObject.CreateInstance<M04Table>();
        table.entries = spec.rows.Where(x => x.kind == "table" || x.kind == "negative_table")
            .Select(x => new M04TableEntry { key = x.key, value = x.text }).ToArray();
        AssetDatabase.CreateAsset(table, TablePath);
        var hard = new TMP_Text[3];
        var runtime = new TMP_Text[3];
        var controller = new GameObject("M04_Controllers");
        var hardWriter = controller.AddComponent<M04HardcodedWriter>();
        var runtimeWriter = controller.AddComponent<M04RuntimeWriter>();
        controller.AddComponent<M04DiagnosticWriter>();

        for (int i = 0; i < positives.Length; i++)
        {
            var row = positives[i];
            TextMeshProUGUI label;
            if (row.kind == "prefab")
            {
                // A *real prefab asset*, with a connected scene instance. The player build
                // may keep only flattened scene data. Do not infer prefab origin from m_text.
                label = MakeLabel("M04_" + row.case_id, row.text, i);
                var path = "Assets/M04/Prefabs/" + row.case_id + ".prefab";
                PrefabUtility.SaveAsPrefabAsset(label.gameObject, path);
                UnityEngine.Object.DestroyImmediate(label.gameObject);
                var asset = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                var instance = PrefabUtility.InstantiatePrefab(asset, scene) as GameObject;
                if (instance == null) throw new InvalidOperationException("Could not instantiate " + path);
                instance.transform.SetParent(canvasObj.transform, false);
                label = instance.GetComponent<TextMeshProUGUI>();
                ((RectTransform)instance.transform).anchoredPosition = new Vector2(24, -16 - i * 47);
            }
            else
            {
                label = MakeLabel("M04_" + row.case_id, "...", i);
                label.transform.SetParent(canvasObj.transform, false);
                ((RectTransform)label.transform).anchoredPosition = new Vector2(24, -16 - i * 47);
            }
            if (row.kind == "table")
            {
                var reader = new GameObject("M04_Reader_" + row.case_id).AddComponent<M04TableReader>();
                reader.table = table;
                reader.key = row.key;
                reader.label = label;
            }
            else if (row.kind == "json")
            {
                var reader = new GameObject("M04_Reader_" + row.case_id).AddComponent<M04JsonReader>();
                reader.label = label;
                reader.resourceName = row.resource_name;
                var path = "Assets/Resources/" + row.resource_name + ".json";
                var json = JsonUtility.ToJson(new M04JsonPayload { id = row.key, message = row.text });
                File.WriteAllText(Path.Combine(ProjectRoot, path), json);
            }
            else if (row.kind == "hardcoded")
            {
                hard[row.kind_index] = label;
            }
            else if (row.kind == "runtime")
            {
                runtime[row.kind_index] = label;
            }
        }
        hardWriter.labels = hard;
        runtimeWriter.labels = runtime;
        foreach (var row in spec.rows.Where(x => x.kind == "negative_json"))
        {
            var path = Path.Combine(ProjectRoot, "Assets/Resources/" + row.resource_name + ".json");
            File.WriteAllText(path, JsonUtility.ToJson(new M04JsonPayload { id = row.key, message = row.text }));
        }
        AssetDatabase.Refresh();
        EditorSceneManager.SaveScene(scene, ScenePath);
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
        AssetDatabase.SaveAssets();
        Debug.Log("[M04] Generated 15 positive UI cases and 5 negative controls. Private answer key not used by this Editor script.");
    }

    [MenuItem("Tools/Mod Studio AI/M04/Build Unseen Lab B Windows Mono")]
    public static void BuildMonoWindows()
    {
        if (PlayerSettings.GetScriptingBackend(NamedBuildTarget.Standalone) != ScriptingImplementation.Mono2x)
            throw new InvalidOperationException("Set Scripting Backend = Mono in Windows Player Settings, not IL2CPP.");
        if (AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath) == null)
            throw new InvalidOperationException("First choose Generate Unseen Lab B Scene.");
        var outFile = Path.GetFullPath(Path.Combine(ProjectRoot, "..", "..", "Builds", "UnityTextLabB", "UnityTextLabB.exe"));
        Directory.CreateDirectory(Path.GetDirectoryName(outFile));
        var options = new BuildPlayerOptions
        {
            scenes = new[] { ScenePath },
            locationPathName = outFile,
            target = BuildTarget.StandaloneWindows64,
            options = BuildOptions.None
        };
        var report = BuildPipeline.BuildPlayer(options);
        if (report.summary.result != BuildResult.Succeeded)
            throw new InvalidOperationException("M04 Windows build failed: " + report.summary.result);
        Debug.Log("[M04] Windows Mono build completed: " + outFile);
    }
}
