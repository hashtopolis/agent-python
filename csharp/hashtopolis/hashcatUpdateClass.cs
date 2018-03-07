using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Diagnostics;

namespace hashtopolis
{

    class hashcatUpdateClass
    {

        public class hcUpdateProper
        {
            public string action = "downloadBinary";
            public string type = "cracker";
            public string token = "";
            public int binaryVersionId = 0;
            public int force { set; get; }
            
        }

        public Boolean debugFlag { get; set; }
        public string AppPath { get; set; }
        public _7zClass sevenZip { get; set; }
        public registerClass client { get; set; }
        public int binaryVersionId { get; set; }


        public bool updateCracker()
        {
            hcUpdateProper hcUpd = new hcUpdateProper();
            jsonClass jsonUpd = new jsonClass { debugFlag = debugFlag, connectURL = client.connectURL };
            hcUpd.token = client.tokenID;
            hcUpd.binaryVersionId = binaryVersionId;

            string jsonString = jsonUpd.toJson(hcUpd);
            string ret = jsonUpd.jsonSend(jsonString);

            if (jsonUpd.isJsonSuccess(ret))
            {
                string crackerName = jsonUpd.getRetVar(ret, "name");
                string fullSubDir = Path.Combine(AppPath, crackerName.ToLower(), binaryVersionId.ToString());
                if (!Directory.Exists(fullSubDir)) //We need to download
                {
                    Console.WriteLine("Client doesn't have required cracker...");
                    downloadClass dlClass = new downloadClass();
                    if (client.osID != 1)
                    {
                        dlClass.DownloadFileCurl(jsonUpd.getRetVar(ret, "url"), Path.Combine(AppPath, "crackerClient.7z"));
                    }
                    else
                    {
                        dlClass.DownloadFile(jsonUpd.getRetVar(ret, "url"), Path.Combine(AppPath, "crackerClient.7z"));
                    }

                    if (Directory.Exists(Path.Combine(AppPath, "tmp")))
                    {
                        Directory.Delete(Path.Combine(AppPath, "tmp"), true);
                    }

                    sevenZip.xtract(Path.Combine(AppPath, "crackerClient.7z"), Path.Combine(AppPath, "tmp"));

                    //check if files present

                    string[] files = Directory.GetFiles(Path.Combine(AppPath, "tmp"));
                    if (files.Length != 0)
                    {
                        Directory.Move(Path.Combine(AppPath, "tmp"), fullSubDir);
                    }
                    else
                    {
                        string[] dirs = Directory.GetDirectories(Path.Combine(AppPath, "tmp"));
                        Directory.Move(dirs[0], fullSubDir);
                    }

                    Directory.Delete(Path.Combine(AppPath, "tmp"));
                    string binLocation = Path.Combine(fullSubDir, jsonUpd.getRetVar(ret, "executable"));

                    if (client.osID != 1) //Chmod for non windows
                    {
                        Console.WriteLine("Applying execution permissions to cracker binary");
                        Process.Start("chmod", "+x \"" + binLocation + "\"");
                    }

                    //May need to inplement legacy checks if cracker is hashcat
                }
                else
                {
                    Console.WriteLine("Client already exists, skipping download");
                }
                client.crackerBinary = jsonUpd.getRetVar(ret, "executable");


                if (client.is64Bit)
                {
                    client.crackerBinary = client.crackerBinary.Replace(".", "64.");
                }
                else
                {
                    client.crackerBinary = client.crackerBinary.Replace(".", "32.");
                }
                    


                client.crackerPath = Path.Combine(AppPath, crackerName.ToLower(), binaryVersionId.ToString());
            }

      
            if (Directory.Exists(client.crackerPath))
            {
                return true;
            }
            else
            {
                Console.WriteLine("Could not locate cracker, perhaps manually delete cracker " + binaryVersionId.ToString());
                return false;
            }
        }


        public bool updateHashcat()
        {
            hcUpdateProper hcUpd = new hcUpdateProper();
            jsonClass jsonUpd = new jsonClass { debugFlag = debugFlag, connectURL = client.connectURL };
            hcUpd.token = client.tokenID;
            string hcBinName = "hashcat";
            if (client.osID == 0)
            {
                hcBinName = hcBinName + "64.bin";
            }
            else if (client.osID == 1)
            {
                hcBinName = hcBinName + "64.exe";
            }

            string hcBinLoc = Path.Combine(AppPath, "hashcat", hcBinName);

            if (File.Exists(hcBinLoc))
            {
                hcUpd.force = 0; //HC exists, we don't need to force
            }
            else
            {
                hcUpd.force = 1; //HC doesn't exist, we need to force
            }

            string jsonString = jsonUpd.toJson(hcUpd);
            string ret = jsonUpd.jsonSend(jsonString);

            if (jsonUpd.getRetVar(ret, "version") == "NEW")
            {
                downloadClass dlClass = new downloadClass();

                if (client.osID != 1)
                {
                    dlClass.DownloadFileCurl(jsonUpd.getRetVar(ret, "url"), Path.Combine(AppPath, "hcClient.7z"));
                }
                else
                {
                    dlClass.DownloadFile(jsonUpd.getRetVar(ret, "url"), Path.Combine(AppPath, "hcClient.7z"));
                }

                sevenZip.xtract(Path.Combine(AppPath, "hcClient.7z"), Path.Combine(AppPath, "hcClient"));
                if (Directory.Exists(Path.Combine(AppPath, "hashcat")))
                {
                    Directory.Delete(Path.Combine(AppPath, "hashcat"), true);
                }
                Directory.Move(Path.Combine(AppPath, "hcClient", jsonUpd.getRetVar(ret, "rootdir")), Path.Combine(AppPath, "hashcat"));
                Directory.Delete(Path.Combine(AppPath, "hcClient"));


                if (client.osID != 1) //Chmod for non windows
                {
                    Console.WriteLine("Applying execution permissions to 7zr binary");
                    Process.Start("chmod", "+x \"" + hcBinLoc + "\"");
                }
            }

            if (File.Exists(hcBinLoc))
            {
                return true;
            }

            return false;

        }
       
    }
}
