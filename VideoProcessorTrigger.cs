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
            // Log a message indicating that the blob trigger has been activated
            _logger.LogInformation($"Blob trigger activated for video upload: {name}");

            // Simulate processing the video by reading the blob stream
            using var blobStreamReader = new StreamReader(stream);
            var contentPreview = await blobStreamReader.ReadToEndAsync();

            // Log additional information about the blob
            _logger.LogInformation($"Processing video: {name}");
            _logger.LogInformation($"Preview of data (first 100 chars): {contentPreview.Substring(0, Math.Min(100, contentPreview.Length))}");

            // Indicate processing is complete
            _logger.LogInformation($"Processing completed for video: {name}");
        }
    }
}
