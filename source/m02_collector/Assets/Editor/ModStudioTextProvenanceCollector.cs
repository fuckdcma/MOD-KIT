// Mod Studio AI - Text Provenance Collector v0.1
// Unity 6.3 editor-only. Reads assets, scenes and prefabs; never changes their contents.
// Put this file under Assets/Editor/. Requires TextMeshPro, already present in UnityTextLab.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace ModStudioAI.EditorTools
{
    internal static class TextProvenanceCollector
    {
        private const string MenuPath = "Tools/Mod Studio AI/Export Text Provenance v0.1";
        private static readonly List<ProvenanceRecord> Records = new List<ProvenanceRecord>();
        private static readonly List<string> Warnings = new List<string>();
        private static readonly HashSet<string> UniqueIds = new HashSet<string>(StringComparer.Ordinal);

        [Serializable]
        private sealed class ProvenanceRecord
        {
            public string record_id;
            public string source_kind;
            public string evidence_kind = "unity_editor_static";
            public string verification = "observed_not_validated";
            public string asset_path;
            public string asset_guid;
            public string asset_local_id;
            public string object_path;
            public string component_type;
            public string source_key;
            public string text;
            public string text_sha256;
            public string prefab_source_path;
            public string prefab_text_difference = "unknown";
            public string font_asset;
            public string material;
            public string shader;
            public string font_atlas;
            public string material_atlas;
            public string atlas_status = "unknown";
            public string note;
        }

        [Serializable]
        private sealed class DialogueDoc
        {
            public string id;
            public string message;
        }

        [Serializable]
        private sealed class Manifest
        {
            public string schema = "modstudio.provenance.v0.1";
            public string created_utc;
            public string project_name;
            public string unity_version;
            public int record_count;
            public int scene_text_count;
            public int prefab_text_count;
            public int scriptable_key_count;
            public int resources_json_count;
            public int warning_count;
            public string[] limitations;
        }

        [MenuItem(MenuPath)]
        private static void Export()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                EditorUtility.DisplayDialog("Mod Studio AI", "Hay thoat Play Mode truoc khi quet.", "OK");
                return;
            }
            // Prevent accidental evidence from an unsaved scene that differs from the on-disk build.
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;

            Records.Clear();
            Warnings.Clear();
            UniqueIds.Clear();
            string projectRoot = Directory.GetParent(Application.dataPath).FullName;
            string outRoot = Path.Combine(projectRoot, "ModStudioExports");
            string outDir = Path.Combine(outRoot, "provenance_" + DateTime.UtcNow.ToString("yyyyMMdd_HHmmss_fff"));
            Directory.CreateDirectory(outDir);

            try
            {
                ScanPrefabs();
                ScanScenes();
                ScanScriptableObjects();
                ScanResourceJson(projectRoot);
                Records.Sort((a, b) => string.CompareOrdinal(a.record_id, b.record_id));

                string jsonl = string.Join("\n", Records.Select(r => JsonUtility.ToJson(r, false))) + "\n";
                File.WriteAllText(Path.Combine(outDir, "text_provenance.jsonl"), jsonl, new UTF8Encoding(false));
                File.WriteAllText(Path.Combine(outDir, "warnings.txt"),
                    Warnings.Count == 0 ? "(none)\n" : string.Join("\n", Warnings) + "\n", new UTF8Encoding(false));

                Manifest m = new Manifest
                {
                    created_utc = DateTime.UtcNow.ToString("o"),
                    project_name = Application.productName,
                    unity_version = Application.unityVersion,
                    record_count = Records.Count,
                    scene_text_count = Records.Count(x => x.source_kind == "scene_tmp_serialized"),
                    prefab_text_count = Records.Count(x => x.source_kind == "prefab_tmp_serialized"),
                    scriptable_key_count = Records.Count(x => x.source_kind == "scriptable_object_kv"),
                    resources_json_count = Records.Count(x => x.source_kind == "resources_json_message"),
                    warning_count = Warnings.Count,
                    limitations = new[]
                    {
                        "Scene and prefab TMP values are editor-time snapshots, not runtime text provenance.",
                        "Resources JSON parser v0.1 supports objects with id:string and message:string only.",
                        "ScriptableObject parser v0.1 supports entries[] with key/value string fields only.",
                        "Managed hardcoded and runtime-generated strings must come from REA CIL and runtime logs.",
                        "No Unity assets, loaded prefabs, or scene files are written by this collector."
                    }
                };
                File.WriteAllText(Path.Combine(outDir, "manifest.json"), JsonUtility.ToJson(m, true) + "\n", new UTF8Encoding(false));
                Debug.Log("[ModStudioAI] Provenance export: " + outDir + " | records=" + m.record_count + " warnings=" + m.warning_count);
                EditorUtility.RevealInFinder(outDir);
                EditorUtility.DisplayDialog("Mod Studio AI", "Export thanh cong!\nRecords: " + m.record_count +
                    "\nWarnings: " + m.warning_count + "\n" + outDir, "OK");
            }
            catch (Exception ex)
            {
                Debug.LogException(ex);
                EditorUtility.DisplayDialog("Mod Studio AI", "Export gap loi. Xem Console va output: " + outDir, "OK");
            }
            finally
            {
                Records.Clear();
                UniqueIds.Clear();
            }
        }

        private static void ScanPrefabs()
        {
            foreach (string guid in AssetDatabase.FindAssets("t:Prefab", new[] { "Assets" }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                GameObject root = null;
                try
                {
                    root = PrefabUtility.LoadPrefabContents(path);
                    if (root == null) { Warnings.Add("Prefab could not load: " + path); continue; }
                    foreach (TMP_Text component in root.GetComponentsInChildren<TMP_Text>(true))
                        AddTmp("prefab_tmp_serialized", path, guid, root, component);
                }
                catch (Exception ex) { Warnings.Add("Prefab " + path + ": " + ex.Message); }
                finally
                {
                    if (root != null) PrefabUtility.UnloadPrefabContents(root);
                }
            }
        }

        private static void ScanScenes()
        {
            // Load only scenes currently not open, then unload them. Never use OpenSceneMode.Single.
            foreach (string guid in AssetDatabase.FindAssets("t:Scene", new[] { "Assets" }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                Scene scene = SceneManager.GetSceneByPath(path);
                bool openedHere = !scene.IsValid() || !scene.isLoaded;
                try
                {
                    if (openedHere) scene = EditorSceneManager.OpenScene(path, OpenSceneMode.Additive);
                    foreach (GameObject root in scene.GetRootGameObjects())
                        foreach (TMP_Text component in root.GetComponentsInChildren<TMP_Text>(true))
                            AddTmp("scene_tmp_serialized", path, guid, root, component);
                }
                catch (Exception ex) { Warnings.Add("Scene " + path + ": " + ex.Message); }
                finally
                {
                    if (openedHere && scene.IsValid() && scene.isLoaded)
                        EditorSceneManager.CloseScene(scene, true);
                }
            }
        }

        private static void AddTmp(string kind, string path, string assetGuid, GameObject root, TMP_Text tmp)
        {
            try
            {
                string objectPath = BuildRelativePath(root.transform, tmp.transform);
                string source = "";
                string sourceDifference = "unknown";
                if (kind == "scene_tmp_serialized" && PrefabUtility.IsPartOfPrefabInstance(tmp))
                {
                    TMP_Text original = PrefabUtility.GetCorrespondingObjectFromSource(tmp);
                    if (original != null)
                    {
                        source = AssetDatabase.GetAssetPath(original);
                        sourceDifference = original.text == tmp.text ? "same" : "different";
                    }
                }
                string localId = "";
                string componentGuid;
                long componentLocalId;
                if (AssetDatabase.TryGetGUIDAndLocalFileIdentifier(tmp, out componentGuid, out componentLocalId))
                    localId = componentLocalId.ToString();

                var r = new ProvenanceRecord
                {
                    source_kind = kind, asset_path = path, asset_guid = assetGuid,
                    asset_local_id = localId, object_path = objectPath,
                    component_type = tmp.GetType().FullName,
                    text = tmp.text ?? "", prefab_source_path = source,
                    prefab_text_difference = sourceDifference,
                    note = "Serialized TMP value; runtime scripts may replace it."
                };
                if (tmp.font != null)
                {
                    r.font_asset = tmp.font.name;
                    if (tmp.font.atlasTexture != null) r.font_atlas = tmp.font.atlasTexture.name;
                }
                Material mat = tmp.fontSharedMaterial;
                if (mat != null)
                {
                    r.material = mat.name;
                    if (mat.shader != null) r.shader = mat.shader.name;
                    if (mat.HasProperty("_MainTex"))
                    {
                        Texture tex = mat.GetTexture("_MainTex");
                        if (tex != null) r.material_atlas = tex.name;
                        if (tmp.font != null && tmp.font.atlasTexture != null && tex != null)
                            r.atlas_status = tmp.font.atlasTexture == tex ? "match" : "mismatch";
                    }
                }
                Add(r);
            }
            catch (Exception ex) { Warnings.Add("TMP " + path + ": " + ex.Message); }
        }

        private static void ScanScriptableObjects()
        {
            foreach (string guid in AssetDatabase.FindAssets("t:ScriptableObject", new[] { "Assets" }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                try
                {
                    ScriptableObject asset = AssetDatabase.LoadAssetAtPath<ScriptableObject>(path);
                    if (asset == null) continue;
                    var so = new SerializedObject(asset);
                    SerializedProperty entries = so.FindProperty("entries");
                    if (entries == null || !entries.isArray) continue;
                    for (int i = 0; i < entries.arraySize; i++)
                    {
                        SerializedProperty item = entries.GetArrayElementAtIndex(i);
                        SerializedProperty key = item.FindPropertyRelative("key");
                        SerializedProperty value = item.FindPropertyRelative("value");
                        if (key == null || value == null ||
                            key.propertyType != SerializedPropertyType.String ||
                            value.propertyType != SerializedPropertyType.String) continue;
                        Add(new ProvenanceRecord
                        {
                            source_kind = "scriptable_object_kv", asset_path = path, asset_guid = guid,
                            component_type = asset.GetType().FullName,
                            object_path = "entries[" + i + "]", source_key = key.stringValue,
                            text = value.stringValue,
                            note = "Serialized ScriptableObject key/value entry."
                        });
                    }
                }
                catch (Exception ex) { Warnings.Add("ScriptableObject " + path + ": " + ex.Message); }
            }
        }

        private static void ScanResourceJson(string projectRoot)
        {
            foreach (string guid in AssetDatabase.FindAssets("t:TextAsset", new[] { "Assets" }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (!path.EndsWith(".json", StringComparison.OrdinalIgnoreCase) ||
                    !path.Replace('\\', '/').Contains("/Resources/")) continue;
                try
                {
                    string physicalPath = Path.Combine(projectRoot, path.Replace('/', Path.DirectorySeparatorChar));
                    string raw = File.ReadAllText(physicalPath, Encoding.UTF8);
                    DialogueDoc doc = JsonUtility.FromJson<DialogueDoc>(raw);
                    if (doc == null || string.IsNullOrEmpty(doc.id) || doc.message == null)
                    {
                        Warnings.Add("JSON unsupported schema (expected id/message): " + path);
                        continue;
                    }
                    Add(new ProvenanceRecord
                    {
                        source_kind = "resources_json_message", asset_path = path, asset_guid = guid,
                        object_path = "$.message", source_key = doc.id, text = doc.message,
                        component_type = "TextAsset/JSON",
                        note = "Parsed JSON source document, not verified against runtime display."
                    });
                }
                catch (Exception ex) { Warnings.Add("JSON " + path + ": " + ex.Message); }
            }
        }

        private static string BuildRelativePath(Transform root, Transform target)
        {
            var parts = new List<string>();
            Transform t = target;
            while (t != null)
            {
                parts.Add(t.name);
                if (t == root) break;
                t = t.parent;
            }
            parts.Reverse();
            return string.Join("/", parts);
        }

        private static void Add(ProvenanceRecord r)
        {
            r.text_sha256 = Hash(r.text ?? "");
            // Stable across changes to displayed text; scoped to the asset and object/key location.
            r.record_id = Hash(r.source_kind + "|" + r.asset_path + "|" + r.object_path +
                "|" + r.component_type + "|" + r.source_key).Substring(0, 24);
            if (!UniqueIds.Add(r.record_id))
                Warnings.Add("Duplicate source location: " + r.asset_path + " " + r.object_path);
            Records.Add(r);
        }

        private static string Hash(string value)
        {
            using (SHA256 sha = SHA256.Create())
            {
                byte[] digest = sha.ComputeHash(Encoding.UTF8.GetBytes(value));
                return BitConverter.ToString(digest).Replace("-", "").ToLowerInvariant();
            }
        }
    }
}
