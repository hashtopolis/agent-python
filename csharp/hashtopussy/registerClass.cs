using System;
using System.Collections.Generic;
using System.IO;
using System.Management;
using System.Diagnostics;
using System.Runtime.InteropServices;

public class registerClass
{
    private string tokenPath;
    public string tokenID { get; set; }
    public int osID { get; set; }
    public string connectURL { get; set; }
    public Boolean debugFlag { set; get; }

    //Suppress P/Invoke warning my using NativeMethods
    internal static class NativeMethods
    {
        [DllImport("libc")]
        public static extern int uname(IntPtr buf);
    }

    //Code from Pinta Core Project
    private bool IsRunningOnMac()
    {

        IntPtr buf = IntPtr.Zero;
        try
        {
            buf = Marshal.AllocHGlobal(8192);
            // This is a hacktastic way of getting sysname from uname ()
            if (NativeMethods.uname(buf) == 0)
            {
                string os = Marshal.PtrToStringAnsi(buf);
                if (os == "Darwin")
                    return true;
            }
        }
        catch
        {
        }
        finally
        {
            if (buf != IntPtr.Zero)
                Marshal.FreeHGlobal(buf);
        }
        return false;
    }


    //Detect whether we are running under mono
    private void setOS()
    {
        if (Type.GetType("Mono.Runtime") != null)
        {
            if (!IsRunningOnMac())
            {
                Console.WriteLine("System is Linux");
                osID = 0;
            }
            else
            {
                Console.WriteLine("System is Mac");
                osID = 2;
            }
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
        jsonClass jsC = new jsonClass { debugFlag = true, connectURL = connectURL };

        setOS();

        string machineName = "default";

        List<string> gpuList;
        string CPUModel = "";

        gpuList = new List<string> { };

        if (osID == 1)
        {
            ManagementObjectSearcher searcher = new ManagementObjectSearcher("SELECT Description FROM Win32_VideoController"); //Prep object to query windows GPUs

            //Get Devices (Windows)
            foreach (ManagementObject mo in searcher.Get())
            {
                gpuList.Add(mo.Properties["Description"].Value.ToString().Trim());
            }

            //Get CPU (Windows)
            searcher = new ManagementObjectSearcher("SELECT Name from Win32_Processor"); //Prep object to query windows CPUs
            foreach (ManagementObject mo in searcher.Get())
            {
                gpuList.Add(mo.Properties["Name"].Value.ToString());
            }
            //Get Machine Name (Windows)
            machineName = System.Environment.MachineName;
        }
        else if(osID ==  0)
        {

            //Get GPU Devices (Linux) use lspci to query GPU
            ProcessStartInfo pinfo = new ProcessStartInfo();
            pinfo.FileName = "lspci";
            pinfo.UseShellExecute = false;
            pinfo.RedirectStandardOutput = true;
            Process lspci = new Process();
            lspci.StartInfo = pinfo;
            lspci.Start();
            string searchString = "VGA compatible controller: ";
            while (!lspci.HasExited)
            {
                while (!lspci.StandardOutput.EndOfStream)
                {
                    string stdOut = lspci.StandardOutput.ReadLine();
                    int pozi = stdOut.IndexOf(searchString);
                    if (pozi != -1)
                    {
                        gpuList.Add(stdOut.Substring(pozi + searchString.Length));
                    }
                }
            }

            //Get CPU (Linux) use lscpu to query CPU
            pinfo.FileName = "lscpu";
            pinfo.UseShellExecute = false;
            pinfo.RedirectStandardOutput = true;
            lspci.StartInfo = pinfo;
            lspci.Start();
            searchString = "Model Name: ";
            while (!lspci.HasExited)
            {
                while (!lspci.StandardOutput.EndOfStream)
                {
                    string stdOut = lspci.StandardOutput.ReadLine();
                    int pos = stdOut.IndexOf(searchString);
                    if (pos != -1)
                    {
                        gpuList.Add(stdOut.Substring(pos + searchString.Length));
                    }
                }
            }
            //Get Machine Name (Linux)
            pinfo = new ProcessStartInfo();
            pinfo.FileName = "uname";
            pinfo.Arguments = "-n";
            pinfo.UseShellExecute = false;
            pinfo.RedirectStandardOutput = true;
            Process uname = new Process();
            uname.StartInfo = pinfo;
            uname.Start();
            while (!uname.HasExited)
            {
                while (!uname.StandardOutput.EndOfStream)
                {
                    string stdOut = uname.StandardOutput.ReadLine();
                    machineName = stdOut;
                }
            }
        }
        else if(osID == 2)
        {
            //Get Machine Name (Mac)
            ProcessStartInfo pinfo = new ProcessStartInfo();
            pinfo.FileName = "scutil";
            pinfo.Arguments = " --get ComputerName";
            pinfo.UseShellExecute = false;
            pinfo.RedirectStandardError = true;
            pinfo.RedirectStandardOutput = true;

            Process getMachineName = new Process();
            getMachineName.StartInfo = pinfo;
            getMachineName.Start();
            while (!getMachineName.HasExited)
            {
                while (!getMachineName.StandardOutput.EndOfStream)
                {
                    string stdOut = getMachineName.StandardOutput.ReadLine();
                    machineName = stdOut;
                }
            }

            //Get Devices (Mac)
            pinfo.FileName = "system_profiler";
            pinfo.Arguments = " -detaillevel mini";
            Process getDevices = new Process();
            getDevices.StartInfo = pinfo;

            Console.WriteLine("Please wait while devices are being enumerated...");
            getDevices.Start();
            Boolean triggerRead = false;

            string searchID = "Chipset Model: ";

            while (!getDevices.StandardOutput.EndOfStream)
            {

                string stdOut = getDevices.StandardOutput.ReadLine().TrimEnd();

                if (triggerRead == true)
                {
                    if (stdOut.Contains("Total Number of Cores:")) //Just incase we go past 
                    {
                        break;
                    }
                    if (stdOut.Contains("Hardware:"))
                    {
                        searchID = "Processor Name: ";
                    }
                    int pos = stdOut.IndexOf(searchID);

                    if (pos != -1)
                    {
                        if (searchID == "Chipset Model: ")
                        {

                            gpuList.Add(stdOut.Substring(pos + searchID.Length));

                        }
                        else if (searchID == "Processor Name: ")
                        {
                            CPUModel = stdOut.Substring(pos + searchID.Length);
                            searchID = "Processor Speed: ";
                        }
                        else if (searchID == "Processor Speed: ")
                        {
                            CPUModel = CPUModel + " @ " + stdOut.Substring(pos + searchID.Length);
                            gpuList.Add(CPUModel);
                            break; 
                        }
                    }
                }
                else if (triggerRead == false)
                {
                    if (stdOut.Contains("Graphics/Displays:"))
                    {
                        triggerRead = true;
                    }
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
            jsonClass jsC = new jsonClass { connectURL = connectURL, debugFlag = debugFlag };

            var arrayKey = new Dictionary<string, string>
               {
                   { "action", "login" },
                   { "token",tokenID},
            };
            
            string jsonString = jsC.toJson(arrayKey);
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
