using System.Diagnostics;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace TP.Function
{
    public class VideoProcessorTrigger
    {
        private readonly ILogger<VideoProcessorTrigger> _logger;

        public VideoProcessorTrigger(ILogger<VideoProcessorTrigger> logger)
        {
            _logger = logger;
        }

        [Function(nameof(VideoProcessorTrigger))]
        public async Task Run(
            [BlobTrigger("videos/{name}", Connection = "AzureWebJobsStorage")] Stream stream, 
            string name)
        {
            try
            {
                _logger.LogInformation($"Blob trigger activated for video upload: {name}");

                // Save the uploaded video to a temporary path
                string tempFilePath = $"/tmp/{name}";
                using (var fileStream = File.Create(tempFilePath))
                {
                    await stream.CopyToAsync(fileStream);
                }
                _logger.LogInformation($"Saved video to {tempFilePath}");

                // Define the Python script and arguments
                string pythonScript = "/mnt/c/Users/asadi/Desktop/TeamProject_CTAI/Evaluation/main.py";
                string arguments = $"{pythonScript} {tempFilePath}";

                // Set up the process to call Python
                ProcessStartInfo psi = new ProcessStartInfo
                {
                    FileName = "python3",
                    Arguments = arguments,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                _logger.LogInformation($"Starting Python script: {psi.FileName} {psi.Arguments}");

                // Start the process and capture the output
                using (Process process = Process.Start(psi))
                {
                    string output = await process.StandardOutput.ReadToEndAsync();
                    string error = await process.StandardError.ReadToEndAsync();
                    process.WaitForExit();

                    if (process.ExitCode == 0)
                    {
                        _logger.LogInformation($"Python script output:\n{output}");
                    }
                    else
                    {
                        _logger.LogError($"Python script failed with exit code {process.ExitCode}:\n{error}");
                    }

                    _logger.LogInformation("Python script execution completed.");
                }

                _logger.LogInformation($"Video processing completed for {name}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"An error occurred while processing the video {name}: {ex.Message}");
            }
        }
    }
}



















// using System.Diagnostics;
// using Microsoft.Azure.Functions.Worker;
// using Microsoft.Extensions.Logging;

// namespace TP.Function
// {
//     public class VideoProcessorTrigger
//     {
//         private readonly ILogger<VideoProcessorTrigger> _logger;

//         public VideoProcessorTrigger(ILogger<VideoProcessorTrigger> logger)
//         {
//             _logger = logger;
//         }

//         [Function(nameof(VideoProcessorTrigger))]
//         public async Task Run(
//             [BlobTrigger("videos/{name}", Connection = "AzureWebJobsStorage")] Stream stream, 
//             string name)
//         {
//             try
//             {
//                 _logger.LogInformation($"Blob trigger activated for video upload: {name}");

//                 // Save the uploaded video to a temporary path
//                 string tempFilePath = $"/tmp/{name}";
//                 using (var fileStream = File.Create(tempFilePath))
//                 {
//                     await stream.CopyToAsync(fileStream);
//                 }
//                 _logger.LogInformation($"Saved video to {tempFilePath}");

//                 // Define the Python script and arguments
//                 string pythonScript = "/mnt/c/Users/asadi/Desktop/TeamProject_CTAI/Evaluation/main.py";
//                 string arguments = $"{pythonScript} {tempFilePath}";

//                 // Set up the process to call Python
//                 ProcessStartInfo psi = new ProcessStartInfo
//                 {
//                     FileName = "python3",
//                     Arguments = arguments,
//                     RedirectStandardOutput = true,
//                     RedirectStandardError = true,
//                     UseShellExecute = false,
//                     CreateNoWindow = true
//                 };

//                 _logger.LogInformation($"Executing Python script: {psi.FileName} {psi.Arguments}");

//                 // Start the process and capture the output
//                 using (Process process = Process.Start(psi))
//                 {
//                     string output = await process.StandardOutput.ReadToEndAsync();
//                     string error = await process.StandardError.ReadToEndAsync();
//                     process.WaitForExit();

//                     if (process.ExitCode == 0)
//                     {
//                         _logger.LogInformation($"Python script output:\n{output}");
//                         Console.WriteLine(output); // Optional: Print to console for local debug
//                     }
//                     else
//                     {
//                         _logger.LogError($"Python script failed with exit code {process.ExitCode}:\n{error}");
//                     }
//                 }

//                 _logger.LogInformation($"Video processing completed for {name}");
//             }
//             catch (Exception ex)
//             {
//                 _logger.LogError($"An error occurred while processing the video {name}: {ex.Message}");
//             }
//         }
//     }
// }
