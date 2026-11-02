using TMPro;
using UnityEngine;

namespace ModStudioLab
{
    public class RuntimeTextExample : MonoBehaviour
    {
        [SerializeField] private TMP_Text label;
        private int health = 75;
        private float elapsed;

        private void Start() { Refresh(); }

        private void Update()
        {
            elapsed += Time.deltaTime;
            if (elapsed < 2f || health <= 0) return;
            elapsed = 0f;
            health = Mathf.Max(0, health - 5);
            Refresh();
        }

        private void Refresh()
        {
            if (label != null) label.text = $"Health: {health}/100";
        }
    }
}
