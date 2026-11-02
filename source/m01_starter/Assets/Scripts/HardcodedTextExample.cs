using TMPro;
using UnityEngine;

namespace ModStudioLab
{
    public class HardcodedTextExample : MonoBehaviour
    {
        [SerializeField] private TMP_Text label;

        private void Awake()
        {
            if (label != null) label.text = "Quest Completed";
            else Debug.LogError("[ModStudioLab] HardcodedTextExample: missing label.");
        }
    }
}