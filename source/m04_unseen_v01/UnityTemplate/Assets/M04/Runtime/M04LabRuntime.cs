using System;
using TMPro;
using UnityEngine;

namespace ModStudioM04
{
    [Serializable]
    public class M04TableEntry
    {
        public string key;
        public string value;
    }

    public sealed class M04Table : ScriptableObject
    {
        public M04TableEntry[] entries;

        public bool TryGet(string id, out string value)
        {
            if (entries != null)
            {
                foreach (var entry in entries)
                {
                    if (entry != null && string.Equals(entry.key, id, StringComparison.Ordinal))
                    {
                        value = entry.value;
                        return true;
                    }
                }
            }
            value = null;
            return false;
        }
    }

    public sealed class M04TableReader : MonoBehaviour
    {
        public M04Table table;
        public TMP_Text label;
        public string key;
        private void Start()
        {
            if (label == null || table == null) return;
            string value;
            if (table.TryGet(key, out value)) label.text = value;
        }
    }

    [Serializable]
    public sealed class M04JsonPayload
    {
        public string id;
        public string message;
    }

    public sealed class M04JsonReader : MonoBehaviour
    {
        public string resourceName;
        public TMP_Text label;
        private void Start()
        {
            if (label == null) return;
            var data = Resources.Load<TextAsset>(resourceName);
            if (data == null) return;
            var payload = JsonUtility.FromJson<M04JsonPayload>(data.text);
            if (payload != null && payload.message != null) label.text = payload.message;
        }
    }
}
