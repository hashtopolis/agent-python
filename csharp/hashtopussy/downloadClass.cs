using System;
using System.Diagnostics;
using System.Net;
using System.Threading;
using System.IO;
using System.ComponentModel;

namespace hashtopolis
{
    class downloadClass
    {


        Stopwatch sw = new Stopwatch();
        private bool completedFlag = false;

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

            completedFlag = false;
            WebClient webClient;
            try
            {
                System.Net.ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls | SecurityProtocolType.Tls11 |
                                                                  SecurityProtocolType.Tls12 | SecurityProtocolType.Ssl3;
            }
            catch
            {
                Console.WriteLine("Skipping TLS settings (consider upgrading to the latest .NET framework for better TLS support");
            }

            using (webClient = new WebClient())
            {
                webClient.DownloadProgressChanged += new DownloadProgressChangedEventHandler(ProgressChanged);
                webClient.DownloadFileCompleted += new AsyncCompletedEventHandler(dlFinished);
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

                //webClient.DownloadFile(URL, location);
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
                while (!completedFlag) Thread.Sleep(500);
                
                if (File.Exists(location))
                    {
                    FileInfo f = new FileInfo(location);
                    long size = f.Length;
                    Console.WriteLine();
                    return true;
                }
                else
                {
                    return false;
                }

            }
        }

        //This will fire upon filedownload completion
        void dlFinished(object sender, AsyncCompletedEventArgs e)
        {
            completedFlag = true;
        }

        // The event that will fire whenever the progress of the WebClient is changed
        private void ProgressChanged(object sender, DownloadProgressChangedEventArgs e)
        {

            double speed = e.BytesReceived / 1024d / sw.Elapsed.TotalSeconds;
            int divCount = 0;
            while (speed > 1000)
            {
                speed = speed / 1000;
                divCount += 1;
            }

            string speedMetric = "?/s";
            switch (divCount)
            {
                case 0:
                    speedMetric = "KB/s";
                        break;
                case 1:
                    speedMetric = "MB/s";
                        break;
                case 2:
                    speedMetric = "GB/s";
                        break;
                case 3:
                    speedMetric = "TB/s";
                    break;
                
            }

            Console.Write("\r{0} {1}% @ {2} {3}", "Downloading",e.ProgressPercentage, speed.ToString("0.00"), speedMetric);

        }


    }
}
