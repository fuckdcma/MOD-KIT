using TMPro;
using UnityEngine;

namespace ModStudioLab
{
    public class TableTextExample : MonoBehaviour
    {
        [SerializeField] private LabStringTable table;
        [SerializeField] private string key = "menu.load";
        [SerializeField] private TMP_Text label;

        private void Start()
        {
            if (label == null || table == null)
            {
                Debug.LogError("[ModStudioLab] TableTextExample: missing reference.");
                return;
            }
            if (table.TryGet(key, out string value)) label.text = value;
            else Debug.LogError("[ModStudioLab] Missing table key: " + key);
        }
    }
}