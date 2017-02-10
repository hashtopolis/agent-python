using System;
using System.Collections.Generic;
using System.IO;
using System.Management;


public class tokenClass
{
    private string tokenPath;
    private string token;

    public void setPath(string path)
    {
        tokenPath = Path.Combine(path,"token");
    }
   
    public string retToken()
    {
        return token;
    }

    public class Register
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

        ManagementObjectSearcher searcher = new ManagementObjectSearcher("SELECT Description FROM Win32_VideoController"); //Prep object to query windows GPUs
        List<string> gpuList;

        gpuList = new List<string> { };
        foreach (ManagementObject mo in searcher.Get())
        {
            gpuList.Add(mo.Properties["Description"].Value.ToString().Trim()); //Add all GPU names to list
        }
        String guid = Guid.NewGuid().ToString(); //Generate GUID

        Register regist = new Register
            {
                action = "register",
                voucher = iVoucher,
            //name = System.Environment.MachineName,
            name = "Gabe",
            uid = guid,
                os = 1, //Hard-code windows
                gpus = gpuList
            };

            string jsonString = jsC.toJson(regist);
            string ret = jsC.jsonSend(jsonString);

            if (jsC.isJsonSuccess(ret))
            {
                token = jsC.getRetVar(ret,"token");
                File.WriteAllText(tokenPath, token);
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
            Console.WriteLine("Token Loaded");


            jsonClass jsC = new jsonClass();

            var arrayKey = new Dictionary<string, string>
               {
                   { "action", "login" },
                   { "token",token},
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
            token = File.ReadAllText(tokenPath);
            if (token == "")
            {
                File.Delete(tokenPath);
                return false;
            }
        }
        else
        {
            return false;
        }
        return true;
    }

}
