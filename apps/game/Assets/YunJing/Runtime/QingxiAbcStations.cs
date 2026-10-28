using QingxiWorld;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace YunJing
{
    // F-key stations that connect the collaborator zones to the novice village: the door of
    // joshsu54's alchemy workshop (his AlchemyRoom scene, server-authoritative), Eli-0731's
    // return sorting table, and the ladder of Johnnnny0823's A10 watch platform.
    public sealed class QingxiAbcStations : MonoBehaviour
    {
        public const string AlchemyScene = "AlchemyRoom";
        public const string VillageScene = "QingxiNoviceVillage";
        const float Reach = 2.4f;

        public Transform alchemyDoor, returnTable;
        public QingxiForestEncounter forest;
        public QingxiFirstPerson walker;

        // Set by QingxiSceneReturn when the player leaves the alchemy room.
        public static bool ReturningFromAlchemy;

        public bool SortingOpen { get; set; }
        public event System.Action SortingRequested;

        void Start()
        {
            if (walker == null) walker = QingxiFirstPerson.Current;
            if (!ReturningFromAlchemy || walker == null || alchemyDoor == null) return;
            ReturningFromAlchemy = false;
            var body = walker.GetComponent<CharacterController>();
            body.enabled = false;
            walker.transform.position = alchemyDoor.position + Vector3.up * .05f;
            walker.transform.rotation = Quaternion.LookRotation(-alchemyDoor.forward);
            body.enabled = true;
            GetComponent<QingxiLocalForaging>()?.RestoreCarried();
        }

        static float Flat(Vector3 a, Vector3 b) => Vector2.Distance(new Vector2(a.x, a.z), new Vector2(b.x, b.z));

        public string Prompt(Vector3 position)
        {
            if (alchemyDoor != null && Flat(position, alchemyDoor.position) <= Reach) return "F 進入溪畔丹房（joshsu54 煉製玩法，需本機 API）";
            if (returnTable != null && Flat(position, returnTable.position) <= Reach) return "F 在分揀桌整理回村樣本（保存／留待煉製／交委託展示）";
            if (forest != null && forest.NearLadder(position)) return forest.Climbed ? "F 爬下觀察台" : "F 爬上觀察台（安全點）";
            return null;
        }

        public bool TryInteract(Vector3 position, out string message)
        {
            message = null;
            if (alchemyDoor != null && Flat(position, alchemyDoor.position) <= Reach)
            {
                if (!Application.CanStreamedLevelBeLoaded(AlchemyScene)) { message = "丹房場景未包含在這個建置"; return true; }
                GetComponent<QingxiLocalForaging>()?.Carry();
                QingxiSceneReturn.ReturnScene = SceneManager.GetActiveScene().name;
                SceneManager.LoadScene(AlchemyScene);
                message = "進入丹房";
                return true;
            }
            if (returnTable != null && Flat(position, returnTable.position) <= Reach)
            {
                SortingRequested?.Invoke();
                message = "攤開分揀桌：三份樣本可自由選去向";
                return true;
            }
            if (forest != null && forest.NearLadder(position)) { message = forest.ToggleClimb(); return true; }
            return false;
        }
    }
}
