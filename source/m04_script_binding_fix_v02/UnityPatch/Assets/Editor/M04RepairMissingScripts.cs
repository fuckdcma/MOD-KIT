// M04 v0.2 — repair script bindings in an existing, locally seeded holdout.
// Never prints or exports private case text, seed or key/value pairs.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using ModStudioM04;
using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class M04RepairMissingScripts
{
    private const string ScenePath = "Assets/M04/Scenes/UnseenLabB.unity";
    private const string TablePath = "Assets/M04/Data/M04HoldoutTable.asset";
    private const string SpecFileName = "M04HoldoutLocal.json";

    private static string ProjectRoot { get { return Directory.GetParent(Application.dataPath).FullName; } }

    private static M04Spec LoadPrivateSpec()
    {
        string path = Path.Combine(ProjectRoot, "ProjectSettings", SpecFileName);
        if (!File.Exists(path)) throw new InvalidOperationException("M04 local specification is missing. Do not regenerate the seed.");
        var spec = JsonUtility.FromJson<M04Spec>(File.ReadAllText(path));
        if (spec == null || spec.rows == null || spec.rows.Length != 20)
            throw new InvalidOperationException("M04 specification should contain 20 rows.");
        if (spec.rows.Count(x => x.kind == "table") != 3 ||
            spec.rows.Count(x => x.kind == "json") != 3 ||
            spec.rows.Count(x => x.kind == "negative_table") != 1)
            throw new InvalidOperationException("M04 specification has an unexpected distribution of reader cases.");
        return spec;
    }

    private static Scene RequireScene()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode)
            throw new InvalidOperationException("Exit Unity Play mode before repairing or validating M04.");
        Scene scene = SceneManager.GetActiveScene();
        if (!scene.IsValid() || !scene.isLoaded || scene.path != ScenePath)
            throw new InvalidOperationException("Open the original Assets/M04/Scenes/UnseenLabB.unity scene first.");
        return scene;
    }

    private static void RequireMonoScripts()
    {
        CheckScript("Assets/M04/Runtime/M04Table.cs", typeof(M04Table));
        CheckScript("Assets/M04/Runtime/M04TableReader.cs", typeof(M04TableReader));
        CheckScript("Assets/M04/Runtime/M04JsonReader.cs", typeof(M04JsonReader));
    }

    private static void CheckScript(string path, Type expected)
    {
        var script = AssetDatabase.LoadAssetAtPath<MonoScript>(path);
        if (script == null || script.GetClass() != expected)
            throw new InvalidOperationException("Unity has not imported a valid script asset for " + path + ". Check Console and let Unity compile.");
    }

    private static GameObject FindUnique(Scene scene, string name)
    {
        var matches = new List<GameObject>();
        foreach (var root in scene.GetRootGameObjects()) CollectByName(root.transform, name, matches);
        if (matches.Count != 1)
            throw new InvalidOperationException("Expected exactly one scene GameObject named " + name + ", found " + matches.Count);
        return matches[0];
    }

    private static void CollectByName(Transform node, string name, List<GameObject> found)
    {
        if (node.name == name) found.Add(node.gameObject);
        for (int i = 0; i < node.childCount; i++) CollectByName(node.GetChild(i), name, found);
    }

    private static IEnumerable<GameObject> TraverseScene(Scene scene)
    {
        var stack = new Stack<Transform>();
        foreach (var root in scene.GetRootGameObjects()) stack.Push(root.transform);
        while (stack.Count != 0)
        {
            var t = stack.Pop();
            yield return t.gameObject;
            for (int i = 0; i < t.childCount; i++) stack.Push(t.GetChild(i));
        }
    }

    private static string PrivateRepairBackupFolder()
    {
        // Stored under ProjectSettings, not Assets. The backed-up .asset can contain secret strings.
        var dir = Path.Combine(ProjectRoot, "ProjectSettings", "M04RepairBackups",
            "repair_" + DateTime.UtcNow.ToString("yyyyMMdd_HHmmss_fff"));
        Directory.CreateDirectory(dir);
        return dir;
    }

    private static M04Table RebuildTable(M04Spec spec)
    {
        string oldPath = Path.Combine(ProjectRoot, TablePath.Replace('/', Path.DirectorySeparatorChar));
        string folder = PrivateRepairBackupFolder();
        if (File.Exists(oldPath)) File.Copy(oldPath, Path.Combine(folder, "M04HoldoutTable.asset"), false);
        if (File.Exists(oldPath + ".meta")) File.Copy(oldPath + ".meta", Path.Combine(folder, "M04HoldoutTable.asset.meta"), false);

        // The original asset was bound to a MonoScript in a multi-class .cs file.
        // Recreate this single asset, then rebind all six scene reader components.
        if (AssetDatabase.LoadMainAssetAtPath(TablePath) != null || File.Exists(oldPath))
        {
            if (!AssetDatabase.DeleteAsset(TablePath))
                throw new InvalidOperationException("Unable to replace the invalid table asset (original file is backed up under ProjectSettings/M04RepairBackups).");
        }
        var table = ScriptableObject.CreateInstance<M04Table>();
        table.entries = spec.rows.Where(x => x.kind == "table" || x.kind == "negative_table")
            .Select(x => new M04TableEntry { key = x.key, value = x.text }).ToArray();
        AssetDatabase.CreateAsset(table, TablePath);
        EditorUtility.SetDirty(table);
        AssetDatabase.SaveAssets();
        var loaded = AssetDatabase.LoadAssetAtPath<M04Table>(TablePath);
        if (loaded == null) throw new InvalidOperationException("Recreated M04 table could not be loaded. Check Unity Console.");
        return loaded;
    }

    [MenuItem("Tools/Mod Studio AI/M04/Repair Missing Script Bindings")]
    public static void RepairMenu()
    {
        Scene scene = RequireScene();
        M04Spec spec = LoadPrivateSpec();
        RequireMonoScripts();
        // Prevalidate all six GameObjects before mutating the table asset.
        var rows = spec.rows.Where(x => x.kind == "table" || x.kind == "json").ToArray();
        foreach (var row in rows)
        {
            FindUnique(scene, "M04_Reader_" + row.case_id);
            var label = FindUnique(scene, "M04_" + row.case_id).GetComponent<TMP_Text>();
            if (label == null) throw new InvalidOperationException("Missing TMP UI label for case " + row.case_id);
        }
        if (!EditorUtility.DisplayDialog("Repair M04 holdout script bindings",
                "Repair 6 reader components and recreate 1 ScriptableObject asset using the EXISTING local specification?\n" +
                "The original table asset and .meta will be backed up under ProjectSettings/M04RepairBackups.\n" +
                "Seed, spec, generated source, private ground truth and all UI strings are preserved.\n" +
                "Do this BEFORE sealing/evaluating a build.",
                "Repair", "Cancel")) return;
        M04Table table = RebuildTable(spec);
        int removed = 0;
        foreach (var row in rows)
        {
            var readerGo = FindUnique(scene, "M04_Reader_" + row.case_id);
            var label = FindUnique(scene, "M04_" + row.case_id).GetComponent<TMP_Text>();
            removed += GameObjectUtility.RemoveMonoBehavioursWithMissingScript(readerGo);
            if (row.kind == "table")
            {
                var reader = readerGo.GetComponent<M04TableReader>();
                if (reader == null) reader = readerGo.AddComponent<M04TableReader>();
                reader.key = row.key;
                reader.table = table;
                reader.label = label;
                EditorUtility.SetDirty(reader);
            }
            else
            {
                var reader = readerGo.GetComponent<M04JsonReader>();
                if (reader == null) reader = readerGo.AddComponent<M04JsonReader>();
                reader.resourceName = row.resource_name;
                reader.label = label;
                EditorUtility.SetDirty(reader);
            }
            EditorUtility.SetDirty(readerGo);
        }
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
        ValidateBeforeBuild();
        Debug.Log("[M04] Repair OK: 6 reader bindings restored; 1 ScriptableObject recreated; " +
                  removed + " missing reader script component(s) removed. No private case text was logged.");
    }

    [MenuItem("Tools/Mod Studio AI/M04/Validate Scene Bindings")]
    public static void ValidateMenu()
    {
        ValidateBeforeBuild();
        Debug.Log("[M04] Validation OK: 6 reader bindings, table asset, controllers and scene scripts valid.");
    }

    public static void ValidateBeforeBuild()
    {
        Scene scene = RequireScene();
        RequireMonoScripts();
        var spec = LoadPrivateSpec();
        var table = AssetDatabase.LoadAssetAtPath<M04Table>(TablePath);
        if (table == null || table.entries == null || table.entries.Length != 4)
            throw new InvalidOperationException("M04Table asset is missing/invalid; use Repair Missing Script Bindings first.");
        foreach (var row in spec.rows.Where(x => x.kind == "table" || x.kind == "negative_table"))
        {
            if (!table.entries.Any(x => x != null && x.key == row.key && x.value == row.text))
                throw new InvalidOperationException("M04Table entry mismatch; use Repair Missing Script Bindings. No secret values are logged.");
        }
        foreach (var row in spec.rows.Where(x => x.kind == "table" || x.kind == "json"))
        {
            var readerGo = FindUnique(scene, "M04_Reader_" + row.case_id);
            var label = FindUnique(scene, "M04_" + row.case_id).GetComponent<TMP_Text>();
            if (label == null) throw new InvalidOperationException("M04 label missing for " + row.case_id);
            if (row.kind == "table")
            {
                var reader = readerGo.GetComponent<M04TableReader>();
                if (reader == null || reader.table != table || reader.label != label || reader.key != row.key)
                    throw new InvalidOperationException("M04 table reader binding is missing for " + row.case_id);
            }
            else
            {
                var reader = readerGo.GetComponent<M04JsonReader>();
                if (reader == null || reader.label != label || reader.resourceName != row.resource_name)
                    throw new InvalidOperationException("M04 JSON reader binding is missing for " + row.case_id);
            }
        }
        var controllers = FindUnique(scene, "M04_Controllers");
        if (controllers.GetComponent<M04HardcodedWriter>() == null ||
            controllers.GetComponent<M04RuntimeWriter>() == null ||
            controllers.GetComponent<M04DiagnosticWriter>() == null)
            throw new InvalidOperationException("One or more M04 controller scripts are missing. Do not build/evaluate.");
        int missing = 0;
        foreach (var go in TraverseScene(scene)) missing += GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(go);
        if (missing != 0)
            throw new InvalidOperationException("M04 scene still contains " + missing + " missing MonoBehaviour script(s). Repair before build.");
    }
}
