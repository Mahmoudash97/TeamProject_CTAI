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
                string pythonScript = "/mnt/c/Users/asadi/Desktop/TeamProject_CTAI/Evaluation/main.py"; // Ensure this is the correct path to your Python script
                string arguments = $"{pythonScript} {tempFilePath}";

                // Set up the process to call Python
                ProcessStartInfo psi = new ProcessStartInfo
                {
                    FileName = "python3", // Ensure 'python3' is available in the environment
                    Arguments = arguments,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                _logger.LogInformation($"Executing Python script: {psi.FileName} {psi.Arguments}");

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
                        _logger.LogError($"Python script failed:\n{error}");
                    }
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








// using System;
// using System.IO;
// using System.Threading.Tasks;
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
//                 // Log the activation of the Blob Trigger
//                 _logger.LogInformation($"Blob trigger activated for video upload: {name}");

//                 // Check if the stream is valid
//                 if (stream == null || stream.Length == 0)
//                 {
//                     _logger.LogWarning($"Blob {name} is empty or could not be read.");
//                     return;
//                 }

//                 // Simulate processing the video
//                 using var blobStreamReader = new StreamReader(stream);
//                 var contentPreview = await blobStreamReader.ReadToEndAsync();

//                 // Log details about the content
//                 _logger.LogInformation($"Processing video: {name}");
//                 _logger.LogInformation($"Content preview (up to 100 chars): {contentPreview.Substring(0, Math.Min(100, contentPreview.Length))}");

//                 // Simulate successful processing
//                 _logger.LogInformation($"Successfully processed the video: {name}");
//             }
//             catch (Exception ex)
//             {
//                 _logger.LogError($"An error occurred while processing the video {name}: {ex.Message}");
//             }
//         }
//     }
// }
