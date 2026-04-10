import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyChXPOn0PCIVV4UqsxD-bRyQ_9xbA2BJZk",
  authDomain: "uplink-283b8.firebaseapp.com",
  projectId: "uplink-283b8",
  storageBucket: "uplink-283b8.firebasestorage.app",
  messagingSenderId: "609875827788",
  appId: "1:609875827788:web:a13ff90ddbb411859368e9",
  measurementId: "G-MFQ6SG1LYN"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Services
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

// Initialize Analytics (optional, protected for SSR/Non-browser environments)
export const analytics = typeof window !== 'undefined' ? getAnalytics(app) : null;
