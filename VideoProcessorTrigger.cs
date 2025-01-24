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
        public async Task Run([BlobTrigger("videos/{name}", Connection = "AzureWebJobsStorage")] Stream stream, string name)
        {
            using var blobStreamReader = new StreamReader(stream);
            var content = await blobStreamReader.ReadToEndAsync();
            _logger.LogInformation($"C# Blob trigger function Processed blob\n Name: {name} \n Data: {content}");
        }
    }
}
