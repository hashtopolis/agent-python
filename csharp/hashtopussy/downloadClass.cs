using System;
using System.Diagnostics;
using System.Net;
using System.Threading;
using System.IO;


namespace hashtopussy
{
    class downloadClass
    {


        Stopwatch sw = new Stopwatch();


        public bool DownloadFileCurl(string urlAddress, string location)
        {
            string AppPath = AppDomain.CurrentDomain.BaseDirectory;
            ProcessStartInfo pinfo = new ProcessStartInfo();
            pinfo.FileName = "curl";
            pinfo.UseShellExecute = false;
            pinfo.RedirectStandardOutput = true;


            pinfo.WorkingDirectory = AppPath;

            pinfo.Arguments = " " + urlAddress + " -o" + "\"" + location + "\"";

            Process unpak = new Process();
            unpak.StartInfo = pinfo;
            unpak.Start();
            unpak.WaitForExit();
            return true;

        }


        public bool DownloadFile(string urlAddress, string location)
        {

            WebClient webClient;
            System.Net.ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls | SecurityProtocolType.Tls11 | SecurityProtocolType.Tls12 | SecurityProtocolType.Ssl3;

            using (webClient = new WebClient())
            {
                webClient.DownloadProgressChanged += new DownloadProgressChangedEventHandler(ProgressChanged);               

                if (!urlAddress.StartsWith("http", StringComparison.OrdinalIgnoreCase))
                {
                    urlAddress = "https://" + urlAddress;
                }
                Uri URL = null;
                try
                {
                    Console.WriteLine("Downloading from " + urlAddress);
                    URL = new Uri(urlAddress);
                }
                catch
                {
                    Console.WriteLine("Invalid url for downloading");
                    return false;
                }

                webClient.DownloadFile(URL, location);
                // Start the stopwatch which we will be using to calculate the download speed
                sw.Start();

                try
                {
                    // Start downloading the file
                    webClient.DownloadFileAsync(URL, location);

                }
                catch (Exception ex)
                {
                    Console.WriteLine(ex.Message);
                    return false;
                }
                while (webClient.IsBusy) Thread.Sleep(500);
                
                if (File.Exists(location))
                    {
                    FileInfo f = new FileInfo(location);
                    long size = f.Length;
                    //Console.WriteLine(string.Format(" completed @ {0} kb/s", (size / 1024d / sw.Elapsed.TotalSeconds).ToString("0.00")));
                    Console.WriteLine();
                    return true;
                }
                else
                {
                    return false;
                }

            }
        }

        // The event that will fire whenever the progress of the WebClient is changed
        private void ProgressChanged(object sender, DownloadProgressChangedEventArgs e)
        {
            // Calculate download speed and output it to labelSpeed.
            //Console.WriteLine (string.Format("{0} kb/s", (e.BytesReceived / 1024d / sw.Elapsed.TotalSeconds).ToString("0.00")));

            // Update the progressbar percentage only when the value is not the same.
            //Console.WriteLine( e.ProgressPercentage);
            Console.Write("\r{0} {1}% @ {2} kb/s", "Downloading",e.ProgressPercentage, (e.BytesReceived / 1024d / sw.Elapsed.TotalSeconds).ToString("0.00"));
            // Update the label with how much data have been downloaded so far and the total size of the file we are currently downloading
            /*
            Console.WriteLine(string.Format("{0} MB's / {1} MB's",
                (e.BytesReceived / 1024d / 1024d).ToString("0.00"),
                (e.TotalBytesToReceive / 1024d / 1024d).ToString("0.00")));
            */
        }


    }
}
