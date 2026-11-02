using TMPro;
using UnityEngine;

namespace ModStudioM04
{
    public sealed class M04TableReader : MonoBehaviour
    {
        public M04Table table;
        public TMP_Text label;
        public string key;

        private void Start()
        {
            if (table == null || label == null) return;
            string value;
            if (table.TryGet(key, out value)) label.text = value;
        }
    }
}
