# Project: Offline AI Tutor for Rural Colombia

## Problem Statement
**Requirement:** A critical constraint for this educational application is the scarcity of high-performance computers or high-end smartphones in the target environment.

**Task:** Propose and explain three possible solutions—whether computer-based (using a browser without internet) or mobile—to implement this educational application in Spanish. The goal is to help elementary through high school students in remote areas of Colombia understand and solve mathematical problems in a didactic manner, following best practices in mathematics pedagogy for children and adolescents.

---

## Proposed Solution

### Solution 1: "The Classroom Cloud" (Local Client-Server Architecture)

**Best for:** Rural schools that have at least one capable computer (belonging to the teacher or administrator) but where students have very low-end smartphones or tablets.

**Concept:** Instead of installing the AI directly on the student's slow device, we transform the teacher's computer into a local "mini-server."

#### How it works:
1.  **The Server (Teacher's PC):** A desktop application is installed to run the AI model (e.g., Gemma 3n or Gemma 2B) using tools like **Ollama** or **LM Studio** (free software). This PC handles all the "thinking" and processing.
2.  **The Local Network (No Internet):** The teacher creates a local Wi-Fi zone (Hotspot) using their smartphone or a basic router (e.g., a generic TP-Link). **Internet access is not required**; the devices only need to be able to "see" each other on the local network.
3.  **The Client (Student's Phone):** The student opens a web browser (Chrome, Firefox, etc.) on their low-end device and navigates to a local address (e.g., `192.168.1.5:3000`).
4.  **The Experience:** The student sees a lightweight web interface (built with pure HTML/JS). They type in the math problem, which travels over the Wi-Fi to the teacher's PC. The PC solves it and sends back the pedagogical explanation.

#### Educational Advantages:
* **Resource Efficiency:** It consumes no storage and minimal battery on the student's phone. Even a device from 8 years ago will run the interface smoothly.
* **Teacher Supervision:** The teacher has centralized control over the queries being asked and the content being delivered.