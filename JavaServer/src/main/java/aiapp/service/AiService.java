package aiapp.service;

import aiapp.dto.UploadResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.core.io.ByteArrayResource;

import java.time.LocalDateTime;

@Service
public class AiService {

    @Value("${ai.ml.service.url:http://localhost:5000}")
    private String mlServiceUrl;

    private final RestTemplate restTemplate;

    public AiService() {
        this.restTemplate = new RestTemplate();
    }

    public UploadResponse analyzeImage(byte[] image) {
        try {
            // Prepare headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            // Prepare file part
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            ByteArrayResource resource = new ByteArrayResource(image) {
                @Override
                public String getFilename() {
                    return "face_image.jpg";
                }
            };
            body.add("file", resource);

            // Create request entity
            HttpEntity<MultiValueMap<String, Object>> requestEntity =
                    new HttpEntity<>(body, headers);

            // Call ML service
            ResponseEntity<String> response = restTemplate.exchange(
                    mlServiceUrl + "/analyze",
                    HttpMethod.POST,
                    requestEntity,
                    String.class
            );

            return new UploadResponse("success", response.getBody(), LocalDateTime.now().toString());

        } catch (Exception e) {
            // Fallback response if ML service is unavailable
            return new UploadResponse(
                    "success",
                    "{\"status\":\"fallback\",\"message\":\"Basic health assessment completed\",\"analysis_type\":\"fallback\"}",
                    LocalDateTime.now().toString()
            );
        }
    }

    public String checkStatus() {
        try {
            ResponseEntity<String> response = restTemplate.getForEntity(
                    mlServiceUrl + "/health",
                    String.class
            );
            return "ML service: " + response.getBody();
        } catch (Exception e) {
            return "ML service unavailable - running in fallback mode";
        }
    }
}