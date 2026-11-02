using System;
using UnityEngine;

namespace ModStudioM04
{
    [Serializable]
    public sealed class M04TableEntry
    {
        public string key;
        public string value;
    }

    // Each Unity ScriptableObject type must have an unambiguous MonoScript asset.
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
}
