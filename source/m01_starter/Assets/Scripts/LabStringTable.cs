using System;
using UnityEngine;

namespace ModStudioLab
{
    [Serializable]
    public class LabStringEntry
    {
        public string key;
        [TextArea] public string value;
    }

    [CreateAssetMenu(fileName = "LabStringTable", menuName = "ModStudioAI/Lab String Table")]
    public class LabStringTable : ScriptableObject
    {
        public LabStringEntry[] entries;

        public bool TryGet(string key, out string result)
        {
            if (entries != null)
            {
                foreach (var entry in entries)
                {
                    if (entry != null && string.Equals(entry.key, key, StringComparison.Ordinal))
                    {
                        result = entry.value;
                        return true;
                    }
                }
            }
            result = null;
            return false;
        }
    }
}