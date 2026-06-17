const API_BASE_URL = 'http://localhost:8000';

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  // Set default headers
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  const config = {
    ...options,
    headers
  };

  if (config.body && typeof config.body !== 'string') {
    config.body = JSON.stringify(config.body);
  }

  try {
    const response = await fetch(url, config);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Something went wrong');
    }
    
    return data;
  } catch (error) {
    console.error(`API Error on ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  // Authentication
  login: (email, password) => 
    request('/api/auth/login', {
      method: 'POST',
      body: { email, password }
    }),
    
  register: (userData) => 
    request('/api/auth/register', {
      method: 'POST',
      body: userData
    }),

  // User Profile
  updateProfile: (profileData) => 
    request('/api/user/profile', {
      method: 'PUT',
      body: profileData
    }),

  // Courses
  getCourses: () => 
    request('/api/courses'),

  // Quizzes & Practice Sets
  getQuizzes: (email) => 
    request(`/api/quizzes?email=${encodeURIComponent(email)}`),
    
  generateQuiz: (quizData) => 
    request('/api/quizzes/generate', {
      method: 'POST',
      body: quizData
    }),

  // Grading Queue
  getGradingQueue: () => 
    request('/api/grading-queue'),
    
  submitGrade: (id, score, feedback) => 
    request('/api/grading-queue/submit', {
      method: 'POST',
      body: { id, score, feedback }
    }),

  // Schedule & Live Sessions
  getSchedule: () => 
    request('/api/schedule'),
    
  addSession: (sessionData) => 
    request('/api/schedule', {
      method: 'POST',
      body: sessionData
    }),

  // AI Tutor / Mentor Chat History
  getChatHistory: (senderId, tutorId) => 
    request(`/api/chat/history?sender_id=${encodeURIComponent(senderId)}&tutor_id=${encodeURIComponent(tutorId)}`),
    
  saveChatMessage: (messageData) => 
    request('/api/chat/history', {
      method: 'POST',
      body: messageData
    })
};
