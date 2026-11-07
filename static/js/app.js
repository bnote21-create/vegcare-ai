// VegCare AI - Client-side Logic

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const btnChooseFile = document.getElementById('btnChooseFile');
  const btnOpenCamera = document.getElementById('btnOpenCamera');
  const samplesGrid = document.getElementById('samplesGrid');

  const previewContainer = document.getElementById('previewContainer');
  const imagePreview = document.getElementById('imagePreview');
  const resultsContainer = document.getElementById('resultsContainer');
  const engineBadge = document.getElementById('engineBadge');
  const apiNoticeBox = document.getElementById('apiNoticeBox');
  const apiNoticeText = document.getElementById('apiNoticeText');
  const btnNoticeOpenSettings = document.getElementById('btnNoticeOpenSettings');

  if (btnNoticeOpenSettings) {
    btnNoticeOpenSettings.addEventListener('click', () => {
      apiKeyInput.value = localStorage.getItem('vegcare_gemini_key') || '';
      keyTestResult.style.display = 'none';
      settingsModal.classList.add('show');
    });
  }

  // Diagnosis DOM
  const statusBanner = document.getElementById('statusBanner');
  const statusIcon = document.getElementById('statusIcon');
  const statusTitle = document.getElementById('statusTitle');
  const statusSubtitle = document.getElementById('statusSubtitle');
  const confidenceVal = document.getElementById('confidenceVal');

  const badgePlantName = document.getElementById('badgePlantName');
  const badgePart = document.getElementById('badgePart');
  const badgeSeverity = document.getElementById('badgeSeverity');

  const symptomsList = document.getElementById('symptomsList');
  const causesList = document.getElementById('causesList');
  const immediateList = document.getElementById('immediateList');
  const organicList = document.getElementById('organicList');
  const chemicalList = document.getElementById('chemicalList');
  const preventionList = document.getElementById('preventionList');

  const edibilityBox = document.getElementById('edibilityBox');
  const edibilityText = document.getElementById('edibilityText');

  // Toolbar Buttons
  const btnSpeak = document.getElementById('btnSpeak');
  const btnPrint = document.getElementById('btnPrint');
  const btnCopyReport = document.getElementById('btnCopyReport');
  const btnReset = document.getElementById('btnReset');

  // Camera Elements
  const cameraModal = document.getElementById('cameraModal');
  const cameraVideo = document.getElementById('cameraVideo');
  const btnCloseCamera = document.getElementById('btnCloseCamera');
  const btnSwitchCamera = document.getElementById('btnSwitchCamera');
  const btnSnapPhoto = document.getElementById('btnSnapPhoto');
  let cameraStream = null;
  let useFacingMode = 'environment'; // environment (back) or user (front)

  // Encyclopedia Elements
  const encyclopediaModal = document.getElementById('encyclopediaModal');
  const btnOpenEncyclopedia = document.getElementById('btnOpenEncyclopedia');
  const btnCloseEncyclopedia = document.getElementById('btnCloseEncyclopedia');
  const btnCloseEncyclopediaFooter = document.getElementById('btnCloseEncyclopediaFooter');
  const encyclopediaSearch = document.getElementById('encyclopediaSearch');
  const encyclopediaList = document.getElementById('encyclopediaList');
  let allDiseases = [];

  // Settings Elements
  const settingsModal = document.getElementById('settingsModal');
  const btnOpenSettings = document.getElementById('btnOpenSettings');
  const btnCloseSettings = document.getElementById('btnCloseSettings');
  const apiKeyInput = document.getElementById('apiKeyInput');
  const btnSaveSettings = document.getElementById('btnSaveSettings');
  const btnTestKey = document.getElementById('btnTestKey');
  const btnClearKey = document.getElementById('btnClearKey');
  const keyTestResult = document.getElementById('keyTestResult');

  // State
  let currentAnalysis = null;
  let isAnalyzing = false;

  // Load Saved API Key
  const savedKey = localStorage.getItem('vegcare_gemini_key') || '';
  apiKeyInput.value = savedKey;

  // 1. Load Samples
  async function loadSamples() {
    try {
      const res = await fetch('/api/samples');
      const data = await res.json();
      if (data.status === 'success' && data.samples) {
        samplesGrid.innerHTML = '';
        data.samples.forEach(sample => {
          const item = document.createElement('div');
          item.className = 'sample-item';
          item.innerHTML = `
            <img src="/samples/${sample.filename}" alt="${sample.title}">
            <div class="sample-name" title="${sample.title}">${sample.title}</div>
            <span class="sample-tag ${sample.status}">${sample.status_text}</span>
          `;
          item.addEventListener('click', () => {
            selectSample(sample.filename, sample.title);
          });
          samplesGrid.appendChild(item);
        });
      }
    } catch (err) {
      console.error('Failed to load samples:', err);
    }
  }

  // 2. Select & Analyze Sample
  async function selectSample(filename, title) {
    if (isAnalyzing) return;
    const imageUrl = `/samples/${filename}`;
    imagePreview.src = imageUrl;

    showToast(`กำลังโหลดและตรวจภาพ: ${title}`, 'info');

    try {
      const res = await fetch(imageUrl);
      const blob = await res.blob();
      await analyzeImageBlob(blob, filename);
    } catch (err) {
      showToast('ไม่สามารถโหลดภาพตัวอย่างได้: ' + err.message, 'error');
    }
  }

  // 3. Dropzone & File Input Handlers
  btnChooseFile.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('click', () => fileInput.click());

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelected(files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0]);
    }
  });

  function handleFileSelected(file) {
    if (!file.type.startsWith('image/')) {
      showToast('กรุณาเลือกไฟล์รูปภาพเท่านั้น (JPG, PNG, WEBP)', 'error');
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
    };
    reader.readAsDataURL(file);

    analyzeImageBlob(file, file.name);
  }

  // 4. Send Image for Analysis
  async function analyzeImageBlob(blobOrFile, filenameHint = '') {
    if (isAnalyzing) return;
    isAnalyzing = true;

    // Start UI scanning animation
    previewContainer.classList.add('scanning');
    resultsContainer.classList.remove('show');
    apiNoticeBox.style.display = 'none';

    const formData = new FormData();
    formData.append('image', blobOrFile, filenameHint || 'upload.jpg');
    
    const userApiKey = localStorage.getItem('vegcare_gemini_key') || '';
    if (userApiKey) {
      formData.append('api_key', userApiKey);
    }

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      if (data.status === 'success' && data.result) {
        renderAnalysisResult(data.result);
      } else {
        throw new Error(data.message || 'การวิเคราะห์ล้มเหลว');
      }
    } catch (err) {
      showToast('เกิดข้อผิดพลาด: ' + err.message, 'error');
    } finally {
      previewContainer.classList.remove('scanning');
      isAnalyzing = false;
    }
  }

  // 5. Render Diagnosis Result
  function renderAnalysisResult(result) {
    currentAnalysis = result;

    // Engine badge
    if (result.engine === 'gemini_vision') {
      engineBadge.style.display = 'inline-flex';
      engineBadge.innerHTML = '<span>🤖 Gemini 2.5 Flash Vision</span>';
      engineBadge.style.background = '#eff6ff';
      engineBadge.style.color = '#1d4ed8';
    } else {
      engineBadge.style.display = 'inline-flex';
      engineBadge.innerHTML = '<span>🌱 Local Agricultural Engine (ออฟไลน์)</span>';
      engineBadge.style.background = '#f0fdf4';
      engineBadge.style.color = '#15803d';
    }

    // Notice banner
    if (result.api_notice) {
      apiNoticeBox.style.display = 'flex';
      if (apiNoticeText) {
        apiNoticeText.textContent = result.api_notice;
      } else {
        apiNoticeBox.textContent = result.api_notice;
      }
    } else {
      apiNoticeBox.style.display = 'none';
    }

    // Status Banner Style
    statusBanner.className = `status-banner ${result.health_status}`;
    if (result.is_normal) {
      statusIcon.textContent = '✓';
      statusTitle.textContent = result.disease_name_th || 'ผักสมบูรณ์แข็งแรง (ปกติ)';
      statusSubtitle.textContent = 'ไม่พบร่องรอยโรคพืช หรือการทำลายของศัตรูพืช';
    } else {
      statusIcon.textContent = result.health_status === 'danger' ? '!' : '⚠';
      statusTitle.textContent = result.disease_name_th || 'พบความผิดปกติในผัก';
      statusSubtitle.textContent = result.status_label_th || 'กรุณาตรวจสอบอาการและปฏิบัติตามแนวทางการรักษา';
    }

    confidenceVal.textContent = `${result.confidence || 95}%`;

    // Metadata Badges
    badgePlantName.textContent = result.plant_name || 'ผักสวนครัว';
    badgePart.textContent = result.part_analyzed || 'ใบ / ลำต้น';
    badgeSeverity.textContent = result.severity_th || (result.is_normal ? 'ปกติ' : 'ปานกลาง');

    // Populate Lists Helper
    function populateList(ulElement, items) {
      ulElement.innerHTML = '';
      if (!items || items.length === 0) {
        const li = document.createElement('li');
        li.textContent = '-';
        ulElement.appendChild(li);
        return;
      }
      items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        ulElement.appendChild(li);
      });
    }

    populateList(symptomsList, result.symptoms);
    populateList(causesList, result.causes);
    populateList(immediateList, result.immediate_actions);
    populateList(organicList, result.organic_treatment);
    populateList(chemicalList, result.chemical_treatment);
    populateList(preventionList, result.prevention);

    // Edibility
    if (result.edibility) {
      edibilityBox.className = `edibility-callout ${result.edibility.safe ? 'safe' : 'unsafe'}`;
      edibilityBox.querySelector('.edibility-icon').textContent = result.edibility.safe ? '🥗' : '🚫';
      edibilityText.textContent = result.edibility.note_th || (result.edibility.safe ? 'สามารถบริโภคได้ปลอดภัย' : 'ไม่ควรบริโภคส่วนที่เป็นโรค');
    }

    // Show Results
    resultsContainer.classList.add('show');
    showToast('การวิเคราะห์สำเร็จเรียบร้อยแล้ว!', 'success');
  }

  // 6. Camera Functions
  btnOpenCamera.addEventListener('click', async () => {
    cameraModal.classList.add('show');
    await startCamera();
  });

  btnCloseCamera.addEventListener('click', () => {
    stopCamera();
    cameraModal.classList.remove('show');
  });

  btnSwitchCamera.addEventListener('click', async () => {
    useFacingMode = useFacingMode === 'environment' ? 'user' : 'environment';
    await startCamera();
  });

  async function startCamera() {
    stopCamera();
    try {
      const constraints = {
        video: {
          facingMode: useFacingMode,
          width: { ideal: 1280 },
          height: { ideal: 960 }
        }
      };
      cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
      cameraVideo.srcObject = cameraStream;
    } catch (err) {
      showToast('ไม่สามารถเปิดกล้องได้: ' + err.message, 'error');
    }
  }

  function stopCamera() {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
      cameraStream = null;
    }
  }

  btnSnapPhoto.addEventListener('click', () => {
    if (!cameraVideo.videoWidth) return;
    const canvas = document.createElement('canvas');
    canvas.width = cameraVideo.videoWidth;
    canvas.height = cameraVideo.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      stopCamera();
      cameraModal.classList.remove('show');

      imagePreview.src = canvas.toDataURL('image/jpeg');
      analyzeImageBlob(blob, 'camera_capture.jpg');
    }, 'image/jpeg', 0.9);
  });

  // 7. Text-To-Speech (Thai Voice)
  btnSpeak.addEventListener('click', () => {
    if (!currentAnalysis) return;
    if (!('speechSynthesis' in window)) {
      showToast('เบราว์เซอร์นี้ไม่รองรับการอ่านออกเสียง', 'error');
      return;
    }

    window.speechSynthesis.cancel(); // Stop existing

    let textToSpeak = `ผลการวิเคราะห์สุขภาพผัก ${currentAnalysis.plant_name}. สถานะ: ${currentAnalysis.disease_name_th}. `;
    if (currentAnalysis.is_normal) {
      textToSpeak += `ผักมีสุขภาพสมบูรณ์แข็งแรงดี ไม่พบอาการโรคพืช. ปลอดภัยในการรับประทานครับ`;
    } else {
      textToSpeak += `ระดับความรุนแรง ${currentAnalysis.severity_th}. `;
      if (currentAnalysis.immediate_actions && currentAnalysis.immediate_actions.length > 0) {
        textToSpeak += `มาตรการเร่งด่วนคือ: ${currentAnalysis.immediate_actions[0]}. `;
      }
      if (currentAnalysis.organic_treatment && currentAnalysis.organic_treatment.length > 0) {
        textToSpeak += `วิธีรักษาแบบอินทรีย์แนะนำ: ${currentAnalysis.organic_treatment[0]}. `;
      }
    }

    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = 'th-TH';
    utterance.rate = 1.0;

    // Try finding Thai voice
    const voices = window.speechSynthesis.getVoices();
    const thaiVoice = voices.find(v => v.lang.startsWith('th'));
    if (thaiVoice) {
      utterance.voice = thaiVoice;
    }

    window.speechSynthesis.speak(utterance);
    showToast('กำลังอ่านออกเสียงสรุปผล...', 'info');
  });

  // 8. Print / Save PDF
  btnPrint.addEventListener('click', () => {
    window.print();
  });

  // 9. Copy Summary Text
  btnCopyReport.addEventListener('click', () => {
    if (!currentAnalysis) return;
    const summary = `
[รายงานตรวจสุขภาพผัก - VegCare AI]
-----------------------------------------
พืช/ผัก: ${currentAnalysis.plant_name} (${currentAnalysis.plant_name_en || ''})
สถานะ: ${currentAnalysis.is_normal ? 'ปกติ สมบูรณ์' : 'ผิดปกติ'}
โรค/ความผิดปกติ: ${currentAnalysis.disease_name_th}
ความมั่นใจ: ${currentAnalysis.confidence}%
ระดับความรุนแรง: ${currentAnalysis.severity_th}

อาการที่พบ:
${(currentAnalysis.symptoms || []).map(s => '- ' + s).join('\n')}

สาเหตุ:
${(currentAnalysis.causes || []).map(c => '- ' + c).join('\n')}

มาตรการแก้ไขเร่งด่วน:
${(currentAnalysis.immediate_actions || []).map(a => '- ' + a).join('\n')}

วิธีรักษาแบบอินทรีย์:
${(currentAnalysis.organic_treatment || []).map(o => '- ' + o).join('\n')}

การบริโภค:
${currentAnalysis.edibility ? currentAnalysis.edibility.note_th : '-'}
-----------------------------------------
    `.trim();

    navigator.clipboard.writeText(summary).then(() => {
      showToast('คัดลอกรายงานสรุปผลลงคลิปบอร์ดแล้ว', 'success');
    }).catch(err => {
      showToast('ไม่สามารถคัดลอกได้: ' + err.message, 'error');
    });
  });

  // 10. Reset
  btnReset.addEventListener('click', () => {
    fileInput.value = '';
    resultsContainer.classList.remove('show');
    fileInput.click();
  });

  // 11. Encyclopedia Functions
  btnOpenEncyclopedia.addEventListener('click', async () => {
    encyclopediaModal.classList.add('show');
    if (allDiseases.length === 0) {
      await loadEncyclopedia();
    }
  });

  btnCloseEncyclopedia.addEventListener('click', () => encyclopediaModal.classList.remove('show'));
  btnCloseEncyclopediaFooter.addEventListener('click', () => encyclopediaModal.classList.remove('show'));

  async function loadEncyclopedia() {
    try {
      const res = await fetch('/api/diseases');
      const data = await res.json();
      if (data.status === 'success' && data.diseases) {
        allDiseases = data.diseases;
        renderEncyclopedia(allDiseases);
      }
    } catch (err) {
      encyclopediaList.innerHTML = `<p style="color: red;">ไม่สามารถโหลดข้อมูลสารานุกรมได้: ${err.message}</p>`;
    }
  }

  function renderEncyclopedia(diseases) {
    encyclopediaList.innerHTML = '';
    if (diseases.length === 0) {
      encyclopediaList.innerHTML = '<p style="text-align: center; color: #64748b; padding: 2rem;">ไม่พบข้อมูลโรคที่ค้นหา</p>';
      return;
    }

    diseases.forEach(d => {
      const card = document.createElement('div');
      card.className = 'detail-card';
      card.style.marginBottom = '1.25rem';
      card.innerHTML = `
        <div class="detail-header" style="justify-content: space-between;">
          <span><strong>${d.name_th}</strong> (${d.name_en})</span>
          <span class="sample-tag ${d.status}">${d.status_label_th}</span>
        </div>
        <div class="detail-body" style="font-size: 0.9rem;">
          <p style="margin-bottom: 0.5rem;"><strong>พืชที่พบ:</strong> ${d.plant_types ? d.plant_types.join(', ') : '-'}</p>
          <div style="margin-bottom: 0.5rem;">
            <strong>อาการสำคัญ:</strong>
            <ul style="padding-left: 1.25rem; margin-top: 0.25rem;">
              ${(d.symptoms || []).map(s => `<li>${s}</li>`).join('')}
            </ul>
          </div>
          <div>
            <strong>วิธีรักษาแบบอินทรีย์:</strong>
            <ul style="padding-left: 1.25rem; margin-top: 0.25rem; color: #166534;">
              ${(d.organic_treatment || []).map(o => `<li>${o}</li>`).join('')}
            </ul>
          </div>
        </div>
      `;
      encyclopediaList.appendChild(card);
    });
  }

  encyclopediaSearch.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) {
      renderEncyclopedia(allDiseases);
      return;
    }
    const filtered = allDiseases.filter(d => {
      const matchName = (d.name_th && d.name_th.toLowerCase().includes(q)) || (d.name_en && d.name_en.toLowerCase().includes(q));
      const matchPlants = d.plant_types && d.plant_types.some(p => p.toLowerCase().includes(q));
      const matchSymptoms = d.symptoms && d.symptoms.some(s => s.toLowerCase().includes(q));
      return matchName || matchPlants || matchSymptoms;
    });
    renderEncyclopedia(filtered);
  });

  // 12. Settings Modal
  btnOpenSettings.addEventListener('click', () => {
    apiKeyInput.value = localStorage.getItem('vegcare_gemini_key') || '';
    keyTestResult.style.display = 'none';
    settingsModal.classList.add('show');
  });

  btnCloseSettings.addEventListener('click', () => settingsModal.classList.remove('show'));

  btnSaveSettings.addEventListener('click', () => {
    const key = apiKeyInput.value.trim();
    if (key) {
      localStorage.setItem('vegcare_gemini_key', key);
      showToast('บันทึก API Key สำเร็จแล้ว', 'success');
    } else {
      localStorage.removeItem('vegcare_gemini_key');
      showToast('ล้างค่า API Key แล้ว (จะใช้ค่าจากระบบหรือโหมดออฟไลน์)', 'info');
    }
    settingsModal.classList.remove('show');
  });

  btnClearKey.addEventListener('click', () => {
    apiKeyInput.value = '';
    localStorage.removeItem('vegcare_gemini_key');
    keyTestResult.style.display = 'none';
    showToast('ลบ Key เรียบร้อย', 'info');
  });

  btnTestKey.addEventListener('click', async () => {
    const key = apiKeyInput.value.trim();
    if (!key) {
      keyTestResult.style.display = 'block';
      keyTestResult.style.background = '#fef2f2';
      keyTestResult.style.color = '#991b1b';
      keyTestResult.textContent = 'กรุณาใส่ API Key ก่อนทดสอบ';
      return;
    }

    keyTestResult.style.display = 'block';
    keyTestResult.style.background = '#eff6ff';
    keyTestResult.style.color = '#1e40af';
    keyTestResult.textContent = 'กำลังทดสอบเชื่อมต่อกับ Google Gemini...';

    try {
      const res = await fetch('/api/test-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: key })
      });
      const data = await res.json();
      if (data.status === 'success') {
        keyTestResult.style.background = '#ecfdf5';
        keyTestResult.style.color = '#065f46';
        keyTestResult.textContent = '✓ เชื่อมต่อสำเร็จ! API Key สามารถใช้งานได้';
      } else {
        keyTestResult.style.background = '#fef2f2';
        keyTestResult.style.color = '#991b1b';
        keyTestResult.textContent = '✕ เกิดข้อผิดพลาด: ' + data.message;
      }
    } catch (err) {
      keyTestResult.style.background = '#fef2f2';
      keyTestResult.style.color = '#991b1b';
      keyTestResult.textContent = '✕ ไม่สามารถส่งคำขอทดสอบได้: ' + err.message;
    }
  });

  // 13. Mobile / Android Installation Functions
  const btnOpenMobileQR = document.getElementById('btnOpenMobileQR');
  const mobileModal = document.getElementById('mobileModal');
  const btnCloseMobileModal = document.getElementById('btnCloseMobileModal');
  const btnCloseMobileModalFooter = document.getElementById('btnCloseMobileModalFooter');
  const mobileUrlDisplay = document.getElementById('mobileUrlDisplay');
  const btnNativeInstallPrompt = document.getElementById('btnNativeInstallPrompt');
  let deferredInstallPrompt = null;

  if (btnOpenMobileQR) {
    btnOpenMobileQR.addEventListener('click', async () => {
      mobileModal.classList.add('show');
      try {
        const res = await fetch('/api/network');
        const data = await res.json();
        if (data.status === 'success' && data.mobile_url) {
          mobileUrlDisplay.textContent = data.mobile_url;
        }
      } catch (err) {
        console.error('Failed to fetch network info:', err);
      }
    });
  }

  if (btnCloseMobileModal) {
    btnCloseMobileModal.addEventListener('click', () => mobileModal.classList.remove('show'));
  }
  if (btnCloseMobileModalFooter) {
    btnCloseMobileModalFooter.addEventListener('click', () => mobileModal.classList.remove('show'));
  }

  // PWA beforeinstallprompt event (Android Chrome)
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    if (btnNativeInstallPrompt) {
      btnNativeInstallPrompt.style.display = 'inline-flex';
      btnNativeInstallPrompt.addEventListener('click', async () => {
        if (!deferredInstallPrompt) return;
        deferredInstallPrompt.prompt();
        const { outcome } = await deferredInstallPrompt.userChoice;
        if (outcome === 'accepted') {
          showToast('กำลังติดตั้งแอป VegCare AI ลงในเครื่อง...', 'success');
        }
        deferredInstallPrompt = null;
        btnNativeInstallPrompt.style.display = 'none';
        mobileModal.classList.remove('show');
      });
    }
  });

  // Register Service Worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').then((reg) => {
        console.log('VegCare AI Service Worker registered successfully:', reg.scope);
      }).catch((err) => {
        console.log('Service Worker registration failed:', err);
      });
    });
  }

  // 14. Toast Notification Helper
  function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastIcon = document.getElementById('toastIcon');
    const toastMsg = document.getElementById('toastMsg');

    toastMsg.textContent = message;
    if (type === 'success') {
      toastIcon.textContent = '✓';
      toast.style.background = '#065f46';
    } else if (type === 'error') {
      toastIcon.textContent = '✕';
      toast.style.background = '#991b1b';
    } else {
      toastIcon.textContent = 'ℹ';
      toast.style.background = '#1e293b';
    }

    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 3500);
  }

  // Initial Boot
  loadSamples();

  // Run first sample (cabbage_healthy.png) as initial demonstration
  setTimeout(() => {
    selectSample('cabbage_healthy.png', 'ผักกาดขาวสมบูรณ์');
  }, 400);
});
