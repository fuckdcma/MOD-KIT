using TMPro;
using UnityEngine;

namespace ModStudioLab
{
    // Read-only observations. A mismatch is a clue, not automatic proof of a bug.
    public class FontSnapshot : MonoBehaviour
    {
        [SerializeField] private TMP_Text label;

        private void Start()
        {
            if (label == null || label.font == null)
            {
                Debug.LogWarning("[ModStudioLab] No TMP label/font to inspect.");
                return;
            }
            TMP_FontAsset font = label.font;
            Material material = label.fontSharedMaterial;
            Texture fontAtlas = font.atlasTexture;
            Texture materialAtlas = material != null && material.HasProperty("_MainTex")
                ? material.GetTexture("_MainTex") : null;
            string shaderName = material != null && material.shader != null
                ? material.shader.name : "<none>";
            Debug.Log($"[ModStudioLab][SDF] object={label.gameObject.name}; " +
                      $"font={font.name}; material={(material != null ? material.name : "<none>")}; " +
                      $"shader={shaderName}; fontAtlas={(fontAtlas != null ? fontAtlas.name : "<none>")}; " +
                      $"materialAtlas={(materialAtlas != null ? materialAtlas.name : "<none>")}; " +
                      $"sameAtlas={fontAtlas == materialAtlas}");
        }
    }
}