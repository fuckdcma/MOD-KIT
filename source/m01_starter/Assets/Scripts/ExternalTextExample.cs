using System;
using TMPro;
using UnityEngine;

namespace ModStudioLab
{
    [Serializable]
    public class LabDialogue
    {
        public string id;
        public string message;
    }

    public class ExternalTextExample : MonoBehaviour
    {
        [SerializeField] private TMP_Text label;

        private void Start()
        {
            if (label == null) return;
            TextAsset asset = Resources.Load<TextAsset>("dialogue");
            if (asset == null)
            {
                Debug.LogError("[ModStudioLab] Assets/Resources/dialogue.json missing.");
                return;
            }
            try
            {
                LabDialogue record = JsonUtility.FromJson<LabDialogue>(asset.text);
                if (record != null) label.text = record.message;
            }
            catch (Exception ex)
            {
                Debug.LogError("[ModStudioLab] Could not parse dialogue: " + ex.Message);
            }
        }
    }
}