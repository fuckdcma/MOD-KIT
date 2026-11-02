using TMPro;
using UnityEngine;

namespace ModStudioM04
{
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
