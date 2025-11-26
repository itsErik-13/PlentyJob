// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAP20EbB13w5MrvffQ0wRBOz_N5Be1CEVY",
  authDomain: "extrack-5a51d.firebaseapp.com",
  projectId: "extrack-5a51d",
  storageBucket: "extrack-5a51d.firebasestorage.app",
  messagingSenderId: "704995564898",
  appId: "1:704995564898:web:c30c41f980173e82cce03b",
  measurementId: "G-414ZST82NV"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const auth = getAuth(app);
const db = getFirestore(app);

export { auth, db };
