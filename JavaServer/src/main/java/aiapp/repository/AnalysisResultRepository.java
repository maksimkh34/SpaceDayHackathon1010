package aiapp.repository;

import aiapp.entity.AnalysisResult;
import aiapp.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface AnalysisResultRepository extends JpaRepository<AnalysisResult, Long> {
    List<AnalysisResult> findByUser(User user);
}
