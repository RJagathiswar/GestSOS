let mediaStream = null;
let gestureEnabled = false;
let shakeCount = 0;
let lastShakeTime = 0;
let cancelWindow = null;
let pendingTimer = null;

const toast = (msg, ms=2500) => {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), ms);
};

// Theme toggle
const themeBtn = document.getElementById('toggleTheme');
let light = false;
themeBtn.addEventListener('click', () => {
  light = !light;
  if (light) document.documentElement.classList.add('light');
  else document.documentElement.classList.remove('light');
});

// Camera
async function startCamera() {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    const video = document.getElementById('preview');
    video.srcObject = mediaStream;
    toast('Camera enabled');
  } catch (e) {
    console.error(e);
    toast('Camera permission denied');
  }
}
function stopCamera() {
  if (mediaStream) {
    mediaStream.getTracks().forEach(t => t.stop());
    mediaStream = null;
    toast('Camera disabled');
  }
}

// Geolocation helper
function getLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error('Geolocation not supported'));
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({lat: pos.coords.latitude, lng: pos.coords.longitude}),
      (err) => reject(err),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  });
}

// Send SOS to backend
async function sendSOS(category) {
  try {
    const { lat, lng } = await getLocation();
    const res = await fetch('/api/sos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, lat, lng })
    });
    const data = await res.json();
    if (data.ok) {
      toast('✅ SOS sent successfully');
    } else {
      toast('❌ Failed: ' + (data.error || 'unknown'));
    }
    console.log('SOS result:', data);
  } catch (e) {
    console.error(e);
    toast('Location error / permission denied');
  }
}

// Gesture mode
function enableGesture() {
  if (gestureEnabled) {
    window.removeEventListener('devicemotion', onMotion);
    gestureEnabled = false;
    document.getElementById('gestureStatus').textContent = 'Gesture disabled';
    toast('Gesture disabled');
    return;
  }
  if (typeof DeviceMotionEvent === 'undefined') {
    toast('DeviceMotion not supported on this device');
    return;
  }
  window.addEventListener('devicemotion', onMotion);
  gestureEnabled = true;
  document.getElementById('gestureStatus').textContent = 'Listening for 4 shakes...';
  toast('Gesture enabled');
}

function onMotion(event) {
  const acc = event.accelerationIncludingGravity;
  if (!acc) return;
  const magnitude = Math.sqrt(acc.x*acc.x + acc.y*acc.y + acc.z*acc.z);
  const now = Date.now();
  if (magnitude > 20) {
    if (now - lastShakeTime > 500) {
      shakeCount++;
      lastShakeTime = now;
      if (shakeCount >= 4) {
        if (cancelWindow) {
          clearTimeout(pendingTimer);
          cancelWindow = null;
          shakeCount = 0;
          toast('🛑 SOS cancelled');
          return;
        }
        cancelWindow = true;
        shakeCount = 0;
        toast('⏳ SOS in 10s — shake 4x again to cancel');
        pendingTimer = setTimeout(async () => {
          cancelWindow = null;
          try {
            await sendSOS('police');
            toast('🚨 Gesture SOS sent');
          } catch(e) {
            toast('Failed to send SOS');
          }
        }, 10000);
      }
    }
  }
}

window.startCamera = startCamera;
window.stopCamera = stopCamera;
window.enableGesture = enableGesture;
window.sendSOS = sendSOS;
