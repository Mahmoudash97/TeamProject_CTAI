using System;
using System.IO;
using System.Threading.Tasks;
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
                // Log the activation of the Blob Trigger
                _logger.LogInformation($"Blob trigger activated for video upload: {name}");

                // Check if the stream is valid
                if (stream == null || stream.Length == 0)
                {
                    _logger.LogWarning($"Blob {name} is empty or could not be read.");
                    return;
                }

                // Simulate processing the video
                using var blobStreamReader = new StreamReader(stream);
                var contentPreview = await blobStreamReader.ReadToEndAsync();

                // Log details about the content
                _logger.LogInformation($"Processing video: {name}");
                _logger.LogInformation($"Content preview (up to 100 chars): {contentPreview.Substring(0, Math.Min(100, contentPreview.Length))}");

                // Simulate successful processing
                _logger.LogInformation($"Successfully processed the video: {name}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"An error occurred while processing the video {name}: {ex.Message}");
            }
        }
    }
}
