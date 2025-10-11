package aiapp.service;

import aiapp.entity.User;
import aiapp.repository.UserRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Map;

@Service
public class HistoryService {
    private final UserRepository userRepository;
    private final ObjectMapper mapper = new ObjectMapper();

    public HistoryService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public void appendHistory(User user, Map<String, Object> response) {
        try {
            List<Map<String, Object>> history = mapper.readValue(user.getRequestHistory(), List.class);
            history.add(response);
            user.setRequestHistory(mapper.writeValueAsString(history));
            userRepository.save(user);
        } catch (Exception e) {
            throw new RuntimeException("Failed to update history", e);
        }
    }
}
