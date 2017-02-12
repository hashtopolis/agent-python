using System;
using System.Collections.Generic;
using System.IO;
using System.Management;
using System.Diagnostics;

public class registerClass
{
    private string tokenPath;
    public string tokenID { get; set; }
    public int osID { get; set; }

    //Detect whether we are running under mono
    private void setOS()
    {
        if (Type.GetType("Mono.Runtime") != null)
        {
            Console.WriteLine("System is Linux");
            osID = 0;
        }
        else
        {
            Console.WriteLine("System is Windows");
            osID = 1;
        }
    }

    public void setPath(string path)
    {
        tokenPath = Path.Combine(path,"token");
    }

    private class Register
    {
        public string action { get; set; }
        public string voucher { get; set; }
        public string name { get; set; }
        public string uid { get; set; }
        public int os { get; set; }
        public IList<string> gpus { get; set; }
    }

    private bool registerAgent(string iVoucher)
    {
        jsonClass jsC = new jsonClass();

        setOS();

        string machineName = "default";

        ManagementObjectSearcher searcher = new ManagementObjectSearcher("SELECT Description FROM Win32_VideoController"); //Prep object to query windows GPUs
        List<string> gpuList;

        gpuList = new List<string> { };

        if (osID == 1)
        {
            foreach (ManagementObject mo in searcher.Get())
            {
                gpuList.Add(mo.Properties["Description"].Value.ToString().Trim()); //Add all GPU names to list
            }


            machineName = System.Environment.MachineName;
        }
        else if(osID ==  0)
        {
            ProcessStartInfo pinfo = new ProcessStartInfo();
            pinfo.FileName = "lspci";
            pinfo.UseShellExecute = false;
            pinfo.RedirectStandardOutput = true;
            Process lspci = new Process();
            lspci.StartInfo = pinfo;
            lspci.Start();
            while (!lspci.HasExited)
            {
                // dig through the output
                while (!lspci.StandardOutput.EndOfStream)
                {
                    string vystup = lspci.StandardOutput.ReadLine();
                    int pozi = vystup.IndexOf("VGA compatible controller: ");
                    if (pozi != -1)
                    {
                        gpuList.Add(vystup.Substring(pozi + 27));
                    }
                }
            }

            pinfo = new ProcessStartInfo();
            pinfo.FileName = "uname";
            pinfo.Arguments = "-n";
            pinfo.UseShellExecute = false;
            pinfo.RedirectStandardOutput = true;
            Process uname = new Process();
            uname.StartInfo = pinfo;            uname.Start();
            while (!uname.HasExited)
            {
                // dig through the output
                while (!uname.StandardOutput.EndOfStream)
                {
                    string vystup = uname.StandardOutput.ReadLine();
                    machineName = vystup;
                }
            }
        }

        String guid = Guid.NewGuid().ToString(); //Generate GUID

        Register regist = new Register
            {
                action = "register",
                voucher = iVoucher,
                name = machineName,
                uid = guid,
                os = osID, 
                gpus = gpuList
            };

            string jsonString = jsC.toJson(regist);
            string ret = jsC.jsonSend(jsonString);

            if (jsC.isJsonSuccess(ret))
            {
                tokenID = jsC.getRetVar(ret,"token");
                File.WriteAllText(tokenPath, tokenID);
                return true;
            }
            return false;

    }
    public bool loginAgent()
    {
        if (!loadToken())
        {
            Console.WriteLine("Unable to find existing token, please enter voucher");
            while (registerAgent(Console.ReadLine()) == false)
            {
                Console.WriteLine("Invalid voucher, please try again");
                string voucher = Console.ReadLine();
            }


        }
        else
        {
            Console.WriteLine("Existing token found");
            jsonClass jsC = new jsonClass();

            var arrayKey = new Dictionary<string, string>
               {
                   { "action", "login" },
                   { "token",tokenID},
            };
            
            string jsonString = jsC.toJson(arrayKey);
            Console.WriteLine(jsonString);
            string ret = jsC.jsonSend(jsonString);

            if (jsC.isJsonSuccess(ret))
            {
                return true;
            }
            else
            {
                Console.WriteLine("Existing token is invalid, please enter voucher");
                while (registerAgent(Console.ReadLine()) == false)
                {
                    Console.WriteLine("Invalid voucher, please try again");
                    string voucher = Console.ReadLine();
                }
            }
            return false;
        }
        return true;
        
    }

    public bool loadToken()
    {
        if (File.Exists(tokenPath))
        {
            tokenID = File.ReadAllText(tokenPath);
            if (tokenID == "")
            {
                File.Delete(tokenPath);
                return false;
            }
        }
        else
        {
            return false;
        }
        setOS();
        return true;
    }

}
