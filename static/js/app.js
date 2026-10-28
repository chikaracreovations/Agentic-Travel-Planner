document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatContainer = document.getElementById('chat-container');
    const sendBtn = document.getElementById('send-btn');
    const statusIndicator = document.getElementById('status-indicator');
    const statusDot = statusIndicator.querySelector('.status-dot');
    const statusText = statusIndicator.querySelector('.status-text');
    const historyToggle = document.getElementById('history-toggle');
    const historySidebar = document.getElementById('history-sidebar');
    const historyList = document.getElementById('history-list');
    const clearHistoryBtn = document.getElementById('clear-history');
    const newChatBtn = document.getElementById('new-chat-btn'); // New Chat Button

    // Search Modal Elements
    const searchBtn = document.getElementById('search-btn');
    const searchModal = document.getElementById('search-modal');
    const modalSearchInput = document.getElementById('modal-search-input');
    const searchResultsList = document.getElementById('search-results-list');

    // Location & Currency Elements
    const locationPickerBtn = document.getElementById('location-picker-btn');
    const locationModal = document.getElementById('location-modal');
    const closeLocationModalBtn = document.getElementById('close-location-modal-btn');
    const autoDetectLocBtn = document.getElementById('auto-detect-loc-btn');
    const saveLocationBtn = document.getElementById('save-location-btn');
    const locCitySelect = document.getElementById('loc-city-select');
    const locCurrencySelect = document.getElementById('loc-currency-select');
    const userLocationText = document.getElementById('user-location-text');
    const headerLocationFlag = document.getElementById('header-location-flag');

    // Agent Activity Bar (PRD Section 8.4)
    const agentActivityBar = document.getElementById('agent-activity-bar');
    const activityStage = document.getElementById('activity-stage');
    const activityDetail = document.getElementById('activity-detail');
    const stopGenerationBtn = document.getElementById('stop-generation-btn');

    let activeAbortController = null;
    let isProcessing = false;
    let searchHistory = loadSearchHistory();
    let currentConversationId = null;
    let userLocation = loadUserLocation();
    let currentActiveItinerary = null;

    // Initialize location badge
    updateUserLocationBadge();

    // Prompt Chips Click Listener
    document.addEventListener('click', (e) => {
        const chip = e.target.closest('.prompt-chip');
        if (chip && chip.dataset.prompt && userInput && !isProcessing) {
            userInput.value = chip.dataset.prompt;
            chatForm.dispatchEvent(new Event('submit', { cancelable: true }));
        }
    });

    // Location Modal Logic
    if (locationPickerBtn && locationModal) {
        locationPickerBtn.addEventListener('click', () => {
            openLocationModal();
        });

        if (closeLocationModalBtn) {
            closeLocationModalBtn.addEventListener('click', () => {
                closeLocationModal();
            });
        }

        locationModal.addEventListener('click', (e) => {
            if (e.target === locationModal) {
                closeLocationModal();
            }
        });

        if (saveLocationBtn && locCitySelect && locCurrencySelect) {
            saveLocationBtn.addEventListener('click', () => {
                const parts = locCitySelect.value.split('|');
                const airport = parts[0] || 'DEL';
                const city = parts[1] || 'New Delhi';
                const country = parts[2] || 'India';
                const currency = locCurrencySelect.value || 'INR';
                const tz = parts[4] || 'Asia/Kolkata';

                const currencySymbols = { INR: '₹', USD: '$', EUR: '€', AED: 'AED', GBP: '£', THB: '฿', SGD: 'S$' };
                const flags = { India: '🇮🇳', UAE: '🇦🇪', Singapore: '🇸🇬', Thailand: '🇹🇭', UK: '🇬🇧', USA: '🇺🇸' };

                userLocation = {
                    city: city,
                    airport: airport,
                    country: country,
                    currency: currency,
                    currencySymbol: currencySymbols[currency] || currency,
                    flag: flags[country] || '📍',
                    timezone: tz
                };

                saveUserLocation();
                updateUserLocationBadge();
                closeLocationModal();
                showToast(`Location set: ${city} (${currency})`);
            });
        }

        if (autoDetectLocBtn) {
            autoDetectLocBtn.addEventListener('click', () => {
                autoDetectLocation();
            });
        }
    }

    function openLocationModal() {
        if (!locationModal) return;
        locationModal.classList.remove('hidden');
        requestAnimationFrame(() => locationModal.classList.add('active'));

        // Match selects to current userLocation
        if (locCitySelect && userLocation) {
            for (let i = 0; i < locCitySelect.options.length; i++) {
                if (locCitySelect.options[i].value.includes(userLocation.airport) || locCitySelect.options[i].value.includes(userLocation.city)) {
                    locCitySelect.selectedIndex = i;
                    break;
                }
            }
        }
        if (locCurrencySelect && userLocation) {
            locCurrencySelect.value = userLocation.currency || 'INR';
        }
    }

    function closeLocationModal() {
        if (!locationModal) return;
        locationModal.classList.remove('active');
        setTimeout(() => locationModal.classList.add('hidden'), 200);
    }

    function loadUserLocation() {
        const saved = localStorage.getItem('agentic_travel_user_loc');
        if (saved) {
            try { return JSON.parse(saved); } catch (e) { }
        }
        return detectInitialLocation();
    }

    function saveUserLocation() {
        localStorage.setItem('agentic_travel_user_loc', JSON.stringify(userLocation));
    }

    function detectInitialLocation() {
        const tz = (Intl.DateTimeFormat && Intl.DateTimeFormat().resolvedOptions().timeZone) || 'Asia/Kolkata';
        const lang = navigator.language || 'en-IN';
        return {
            city: 'New Delhi',
            airport: 'DEL',
            country: 'India',
            currency: 'INR',
            currencySymbol: '₹',
            flag: '🇮🇳',
            timezone: tz.includes('Kolkata') || tz.includes('Calcutta') ? tz : 'Asia/Kolkata'
        };
    }

    function updateUserLocationBadge() {
        if (!userLocationText) return;
        userLocationText.textContent = `${userLocation.city} (${userLocation.currency} ${userLocation.currencySymbol || '₹'})`;
        if (headerLocationFlag) {
            headerLocationFlag.textContent = userLocation.flag || '🇮🇳';
        }
    }

    async function autoDetectLocation() {
        showToast('Detecting location & currency...');
        const tz = (Intl.DateTimeFormat && Intl.DateTimeFormat().resolvedOptions().timeZone) || 'Asia/Kolkata';

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    try {
                        const res = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`);
                        if (res.ok) {
                            const data = await res.json();
                            const city = data.city || data.locality || 'New Delhi';
                            const country = data.countryName || 'India';
                            const isIndia = country.toLowerCase().includes('india') || data.countryCode === 'IN';
                            userLocation = {
                                city: city,
                                airport: isIndia ? 'DEL' : 'DEL',
                                country: country,
                                currency: isIndia ? 'INR' : 'USD',
                                currencySymbol: isIndia ? '₹' : '$',
                                flag: isIndia ? '🇮🇳' : '🌍',
                                timezone: tz
                            };
                            saveUserLocation();
                            updateUserLocationBadge();
                            showToast(`Detected: ${city}, ${country} (${userLocation.currency})`);
                            closeLocationModal();
                            return;
                        }
                    } catch (err) {
                        console.warn('Reverse geocode failed:', err);
                    }
                    fallbackIndiaDetect(tz);
                },
                (err) => {
                    console.log('Geolocation denied or unavailable, using timezone:', err.message);
                    fallbackIndiaDetect(tz);
                },
                { timeout: 6000 }
            );
        } else {
            fallbackIndiaDetect(tz);
        }
    }

    function fallbackIndiaDetect(tz) {
        userLocation = {
            city: 'New Delhi',
            airport: 'DEL',
            country: 'India',
            currency: 'INR',
            currencySymbol: '₹',
            flag: '🇮🇳',
            timezone: tz || 'Asia/Kolkata'
        };
        saveUserLocation();
        updateUserLocationBadge();
        showToast('Location set: India (INR ₹)');
        closeLocationModal();
    }

    // Search Modal Logic
    if (searchBtn && searchModal) {
        searchBtn.addEventListener('click', () => {
            openSearchModal();
        });

        // Close on outside click
        searchModal.addEventListener('click', (e) => {
            if (e.target === searchModal) {
                closeSearchModal();
            }
        });

        // Search filtering
        modalSearchInput.addEventListener('input', (e) => {
            renderSearchResults(e.target.value);
        });
    }

    function openSearchModal() {
        if (!searchModal) return;
        searchModal.classList.remove('hidden');
        requestAnimationFrame(() => searchModal.classList.add('active'));

        modalSearchInput.value = '';
        modalSearchInput.focus();
        renderSearchResults(); // Show all initially
    }

    function closeSearchModal() {
        if (!searchModal) return;
        searchModal.classList.remove('active');
        setTimeout(() => searchModal.classList.add('hidden'), 200);
    }

    function renderSearchResults(query = '') {
        if (!searchResultsList) return;
        searchResultsList.innerHTML = '';

        const filteredHistory = searchHistory.filter(c =>
            c.title.toLowerCase().includes(query.toLowerCase())
        );

        if (filteredHistory.length === 0) {
            searchResultsList.innerHTML = '<div style="padding: 1rem; color: #888;">No results found</div>';
            return;
        }

        filteredHistory.forEach(conversation => {
            const item = document.createElement('div');
            item.className = 'search-result-item';

            // Format time similarly to image "Today", "Dec 3", etc.
            const timeStr = formatSimpleDate(conversation.timestamp);

            item.innerHTML = `
                <div class="search-result-title">${escapeHtml(conversation.title)}</div>
                <div class="search-result-date">${timeStr}</div>
            `;

            item.addEventListener('click', () => {
                loadConversation(conversation.id);
                closeSearchModal();
                if (window.innerWidth < 768) {
                    historySidebar.classList.add('collapsed');
                }
            });

            searchResultsList.appendChild(item);
        });
    }

    function formatSimpleDate(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (date.toDateString() === now.toDateString()) {
            return 'Today';
        }
        if (diffDays === 1) {
            return 'Yesterday';
        }
        // Return "Dec 3"
        return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    }

    // ...

    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            startNewConversation();
            // On mobile, maybe close sidebar?
            if (window.innerWidth < 768) {
                historySidebar.classList.add('collapsed');
            }
        });
    }
    let conversationMessages = [];

    // Initialize history display
    renderHistory();

    const fileInput = document.getElementById('file-input');
    let selectedFiles = [];  // Array to store multiple files

    // Toggle history sidebar
    historyToggle.addEventListener('click', () => {
        historySidebar.classList.toggle('collapsed');
    });

    const menuBtn = document.getElementById('attach-menu-btn');
    const menu = document.getElementById('attachment-menu');

    // Toggle Menu
    menuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        menu.classList.toggle('active');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!menu.contains(e.target) && !menuBtn.contains(e.target)) {
            menu.classList.remove('active');
        }
    });

    // Handle File Selection (Label triggers input, but we also want to close menu)
    fileInput.addEventListener('click', () => {
        menu.classList.remove('active');
    });

    // Get file type icon based on extension
    function getFileIcon(ext) {
        const icons = {
            'pdf': `<svg class="file-type-icon pdf" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <text x="8" y="17" font-size="6" fill="currentColor" stroke="none">PDF</text>
            </svg>`,
            'docx': `<svg class="file-type-icon doc" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>`,
            'doc': `<svg class="file-type-icon doc" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>`,
            'txt': `<svg class="file-type-icon txt" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>`,
            'default': `<svg class="file-type-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
            </svg>`
        };
        return icons[ext] || icons['default'];
    }

    // Create a pill for a single file
    function createFilePill(file, index) {
        const pill = document.createElement('div');
        pill.className = 'file-pill';
        pill.dataset.fileIndex = index;

        const fileExtension = file.name.split('.').pop().toLowerCase();
        const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(fileExtension);

        if (isImage) {
            // Create thumbnail preview for images
            const reader = new FileReader();
            reader.onload = (e) => {
                pill.innerHTML = `
                    <div class="file-preview">
                        <img src="${e.target.result}" alt="${file.name}" class="file-thumbnail">
                    </div>
                    <span class="file-name">${file.name}</span>
                    <button type="button" class="remove-file">×</button>
                `;
                attachRemoveListener(pill, index);
            };
            reader.readAsDataURL(file);

            // Show loading state
            pill.innerHTML = `
                <div class="file-preview loading">
                    <div class="thumbnail-loader"></div>
                </div>
                <span class="file-name">${file.name}</span>
                <button type="button" class="remove-file">×</button>
            `;
        } else {
            // Show file type icon for documents
            pill.innerHTML = `
                <div class="file-preview">
                    ${getFileIcon(fileExtension)}
                </div>
                <span class="file-name">${file.name}</span>
                <button type="button" class="remove-file">×</button>
            `;
        }

        attachRemoveListener(pill, index);
        return pill;
    }

    // Render all file pills
    function renderFilePills() {
        // Remove all existing pills
        document.querySelectorAll('.file-pill').forEach(pill => pill.remove());

        // Create new pills for each file
        selectedFiles.forEach((file, index) => {
            const pill = createFilePill(file, index);
            chatForm.insertBefore(pill, userInput);
        });
    }

    function attachRemoveListener(pill, index) {
        const removeBtn = pill.querySelector('.remove-file');
        if (removeBtn) {
            removeBtn.onclick = () => {
                // Remove file from array
                selectedFiles.splice(index, 1);
                // Re-render all pills (updates indices)
                renderFilePills();
                // Clear file input if no files left
                if (selectedFiles.length === 0) {
                    fileInput.value = '';
                }
            };
        }
    }

    // File Selection - handles multiple files
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            // Add new files to the array
            for (let i = 0; i < e.target.files.length; i++) {
                selectedFiles.push(e.target.files[i]);
            }
            renderFilePills();
            userInput.focus();
        }
    });

    // Clear history
    // Clear history
    clearHistoryBtn.addEventListener('click', () => {
        showConfirmModal(
            'Clear History',
            'Are you sure you want to clear all search history?',
            () => {
                searchHistory = [];
                saveSearchHistory();
                renderHistory();

                // Also clear all chat messages and start new conversation
                startNewConversation();
            }
        );
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        let message = userInput.value.trim();

        let filesToSend = [];

        // Handle attachment preparation
        if (selectedFiles.length > 0) {
            filesToSend = [...selectedFiles]; // Copy array before resetting

            // Reset UI file input state
            selectedFiles = [];
            fileInput.value = '';
            document.querySelectorAll('.file-pill').forEach(pill => pill.remove());
        }

        if ((!message && filesToSend.length === 0) || isProcessing) return;

        // Switch UI to active conversation mode
        chatContainer.classList.add('has-messages');

        // If starting a new conversation, create a history entry
        if (currentConversationId === null) {
            currentConversationId = Date.now().toString();
            addConversationToHistory(message);
        }

        // Add User Message
        appendMessage('user', message);
        saveCurrentConversation();

        userInput.value = '';
        activeAbortController = new AbortController();
        setProcessing(true);

        try {
            // Prepare FormData for multipart upload
            const formData = new FormData();
            formData.append('message', message);
            // Append all files
            filesToSend.forEach(file => {
                formData.append('file', file);
            });

            const response = await fetch('/api/chat', {
                method: 'POST',
                signal: activeAbortController.signal,
                headers: { 
                    'X-Session-Id': currentConversationId,
                    'X-User-Location': `${userLocation.city}, ${userLocation.country}`,
                    'X-User-Currency': userLocation.currency,
                    'X-User-City': userLocation.city,
                    'X-User-Country': userLocation.country,
                    'X-User-Airport': userLocation.airport,
                    'X-User-Timezone': userLocation.timezone,
                },
                body: formData
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');

                // Process all complete lines
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const event = JSON.parse(line);
                            handleEvent(event);
                        } catch (e) {
                            console.error('Error parsing JSON:', e);
                        }
                    }
                }
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                appendMessage('assistant', 'Plan generation cancelled by user.');
            } else {
                console.error('Error:', error);
                appendMessage('assistant', 'Sorry, something went wrong. Please try again.');
            }
        } finally {
            activeAbortController = null;
            setProcessing(false);
            saveCurrentConversation(); // Save final state
        }
    });

    function handleEvent(event) {
        switch (event.type) {
            case 'message':
                // Only show messages that don't contain raw tool output
                if (!event.content.includes('```tool_outputs')) {
                    appendMessage('assistant', event.content);
                }
                break;
            case 'tool_call':
                appendToolCall(event.name, event.arguments);
                if (typeof highlightAgentByTool === 'function') {
                    highlightAgentByTool(event.name, event.arguments);
                }
                break;
            case 'tool_result':
                // Just update the status, don't display the raw result
                updateToolResult(event.name, event.content, event.is_error);
                break;
            case 'error':
                appendMessage('assistant', `Error: ${event.content}`);
                break;
        }
    }

    const PARTNER_BOOKING_HOSTS = /(aviasales\.com|hotellook\.com|rentalcars\.com|checkout\.stripe\.com)/i;

    function appendMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Linkify markdown links AND raw http(s) URLs in a single pass, then newlines.
        let formattedContent = escapeHtml(content)
            .replace(
                /\[([^\]]+)\]\(([^)]+)\)|(https?:\/\/[^\s<>"]+)/g,
                (_m, mdText, mdUrl, rawUrl) => {
                    const url = mdUrl || rawUrl;
                    const text = mdText || rawUrl;
                    return `<a href="${url}" target="_blank" rel="noopener noreferrer">${text}</a>`;
                }
            )
            .replace(/\n/g, '<br>');

        contentDiv.innerHTML = formattedContent;

        messageDiv.appendChild(contentDiv);
        chatContainer.appendChild(messageDiv);
        scrollToBottom();

        // Auto-open partner booking URLs so the user lands on the provider's
        // checkout page without an extra click. Browsers may block this if no
        // recent user gesture is registered; the inline link above is the
        // fallback in that case.
        if (role === 'assistant') {
            const urls = content.match(/https?:\/\/[^\s<>"]+/g) || [];
            const seen = new Set();
            for (const u of urls) {
                if (!seen.has(u) && PARTNER_BOOKING_HOSTS.test(u)) {
                    seen.add(u);
                    try { window.open(u, '_blank', 'noopener'); } catch (_) { /* popup blocked */ }
                }
            }

            // Fallback parse if itinerary was presented in conversation text
            if (!currentActiveItinerary) {
                parseItineraryFromText(content);
            }
        }

        // Update internal state
        conversationMessages.push({ role, content });
    }

    function appendToolCall(name, args) {
        const toolDiv = document.createElement('div');
        toolDiv.className = 'tool-call';
        toolDiv.id = `tool-${Date.now()}`;

        // Get friendly display text
        const displayInfo = getToolDisplayInfo(name, args);

        toolDiv.innerHTML = `
            <div class="tool-icon">
                ${displayInfo.icon}
            </div>
            <div class="tool-details">
                <div class="tool-name">${displayInfo.title}</div>
                <div class="tool-args">${displayInfo.description}</div>
            </div>
            <div class="tool-status running">${displayInfo.runningText}</div>
        `;

        chatContainer.appendChild(toolDiv);
        scrollToBottom();

        // Update truthful Agent Activity Panel (PRD Section 8.4)
        if (agentActivityBar && activityStage && activityDetail) {
            agentActivityBar.classList.remove('hidden');
            const toolStages = {
                'search_flights': { stage: '✈️ Researching Flights', detail: `${args.origin || 'DEL'} → ${args.destination || 'India'}` },
                'search_hotels': { stage: '🏨 Comparing Accommodations', detail: `Hotels in ${args.city_code || 'destination'}` },
                'rent_car': { stage: '🚗 Car Rentals', detail: `Vehicles in ${args.location || 'destination'}` },
                'get_forecast': { stage: '☀️ Checking Weather', detail: `${args.location || 'destination'}` },
                'calculate_trip_budget': { stage: '💰 Calculating Deterministic Budget', detail: 'Itemizing in ₹ INR' },
                'estimate_standard_budget': { stage: '💰 Estimating Benchmark Costs', detail: 'Applying Indian travel metrics' },
                'validate_itinerary_feasibility': { stage: '📋 Validating Feasibility', detail: 'Verifying schedule buffers & pace' },
                'save_planned_trip': { stage: '💾 Persisting Itinerary', detail: 'Saving to SQLite database' },
            };
            const s = toolStages[name] || { stage: '⚡ Executing Tool', detail: formatToolName(name) };
            activityStage.textContent = s.stage;
            activityDetail.textContent = s.detail;
        }

        window.lastToolDiv = toolDiv;

        conversationMessages.push({
            role: 'tool_call_ui',
            name,
            args,
            displayInfo
        });
    }

    function getToolDisplayInfo(name, args) {
        switch (name) {
            case 'search_flights':
                return {
                    title: 'Flight Search',
                    description: `${args.origin || '?'} → ${args.destination || '?'} on ${args.date || '?'}`,
                    runningText: 'Searching...',
                    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"></path></svg>'
                };
            case 'search_hotels':
                return {
                    title: 'Search Hotels',
                    description: `City: ${args.city_code || '?'}, In: ${args.check_in || '?'}, Adults: ${args.adults || 2}`,
                    runningText: 'Finding stays...',
                    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18M3 7v14M21 7v14M6 3h12a2 2 0 0 1 2 2v2H4V5a2 2 0 0 1 2-2zM8 11h2M14 11h2M8 15h2M14 15h2"></path></svg>'
                };
            case 'calculate_trip_budget':
                return {
                    title: 'Deterministic Budget Calculation',
                    description: `Itemizing total & per-traveler costs in ₹ INR`,
                    runningText: 'Calculating...',
                    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>'
                };
            case 'estimate_standard_budget':
                return {
                    title: 'Standard Budget Benchmark',
                    description: `${args.destination || 'Destination'} (${args.duration_days || '?'} days, ${args.travel_style || 'moderate'})`,
                    runningText: 'Estimating...',
                    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>'
                };
            case 'build_day_by_day_itinerary':
                return {
                    title: 'Day-by-Day Itinerary Builder',
                    description: `${args.destination || 'Destination'} (${args.duration_days || '?'} days, ${args.traveler_count || 1} pax)`,
                    runningText: 'Generating timeline...',
                    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
                };
            case 'get_destination_local_guide':
                return {
                    title: 'Local Transport & Apps Guide',
                    description: `Cabs (GoaMiles/Rapido/Uber), food & transit for ${args.destination || 'destination'}`,
                    runningText: 'Fetching local guide...',
                    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8z"></path><circle cx="12" cy="10" r="3"></circle></svg>'
                };
            case 'validate_itinerary_feasibility':
                return {
                    title: 'Feasibility & Constraint Validation',
                    description: `Auditing active hours, pace (${args.travel_pace || 'moderate'}), and transit`,
                    runningText: 'Auditing...',
                    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
                };
            case 'save_planned_trip':
                return {
                    title: 'Save Trip Itinerary',
                    description: `Saving '${args.title || 'Trip'}' to local storage`,
                    runningText: 'Saving...',
                    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>'
                };
            case 'get_forecast':
                return {
                    title: 'Weather Forecast',
                    description: `${args.location || '?'} on ${args.date || '?'}`,
                    runningText: 'Checking weather...',
                    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path><circle cx="12" cy="12" r="5"></circle></svg>'
                };
            case 'rent_car':
                return {
                    title: 'Car Rental',
                    description: `${args.location || '?'} from ${args.start_date || '?'} to ${args.end_date || '?'}`,
                    runningText: 'Searching cars...',
                    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"></path><circle cx="7" cy="17" r="2"></circle><path d="M9 17h6"></path><circle cx="17" cy="17" r="2"></circle></svg>'
                };
            case 'book_flight':
                return {
                    title: 'Flight Booking',
                    description: `Booking for ${args.passenger_name || '?'}`,
                    runningText: 'Booking...',
                    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"></path></svg>'
                };
            default:
                return {
                    title: formatToolName(name),
                    description: JSON.stringify(args),
                    runningText: 'Running...',
                    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
                };
        }
    }

    function updateToolResult(name, content, isError) {
        if (window.lastToolDiv) {
            const statusDiv = window.lastToolDiv.querySelector('.tool-status');
            statusDiv.classList.remove('running');

            if (isError) {
                statusDiv.textContent = 'Error';
                statusDiv.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
                statusDiv.style.color = '#ef4444';
            } else {
                statusDiv.textContent = 'Completed';
                statusDiv.style.backgroundColor = 'rgba(34, 197, 94, 0.1)';
                statusDiv.style.color = '#22c55e';
            }
            window.lastToolDiv = null;
        }

        // Live Workspace Updates (PRD Section 8.3)
        try {
            let data = null;
            if (typeof content === 'string') {
                data = JSON.parse(content);
            } else if (typeof content === 'object') {
                data = content;
            }
            if (data && !isError) {
                if (name === 'calculate_trip_budget' || name === 'estimate_standard_budget') {
                    updateBudgetWorkspace(data);
                } else if (name === 'search_flights') {
                    updateFlightsWorkspace(data);
                } else if (name === 'search_hotels') {
                    updateHotelsWorkspace(data);
                } else if (name === 'build_day_by_day_itinerary') {
                    updateItineraryWorkspace(data);
                    loadSavedTrips();
                } else if (name === 'save_planned_trip') {
                    loadSavedTrips();
                }
            }
        } catch (_) {}
    }

    function formatToolName(name) {
        return name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    }

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function setProcessing(processing) {
        isProcessing = processing;
        userInput.disabled = processing;
        sendBtn.disabled = processing;

        if (processing) {
            statusDot.classList.add('busy');
            statusText.textContent = 'Thinking...';

            if (agentActivityBar) {
                agentActivityBar.classList.remove('hidden');
                if (activityStage) activityStage.textContent = 'Planning & Orchestrating...';
                if (activityDetail) activityDetail.textContent = 'Evaluating constraints & travel preferences';
            }

            // Add "Thinking" bubble
            const thinkingDiv = document.createElement('div');
            thinkingDiv.className = 'message assistant thinking-bubble';
            thinkingDiv.id = 'thinking-indicator';
            thinkingDiv.innerHTML = `
                <div class="message-content">
                    <div class="thinking-wrapper">
                        <span class="thinking-text">Thinking</span>
                        <div class="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            `;
            chatContainer.appendChild(thinkingDiv);
            scrollToBottom();
        } else {
            statusDot.classList.remove('busy');
            statusText.textContent = 'Ready';
            userInput.focus();

            if (agentActivityBar) {
                agentActivityBar.classList.add('hidden');
            }

            // Remove "Thinking" bubble
            const thinkingDiv = document.getElementById('thinking-indicator');
            if (thinkingDiv) {
                thinkingDiv.remove();
            }
        }
    }

    // Search History Functions
    function loadSearchHistory() {
        try {
            const saved = localStorage.getItem('travelSearchHistory');
            return saved ? JSON.parse(saved) : [];
        } catch (e) {
            console.error('Error loading search history:', e);
            return [];
        }
    }

    function saveSearchHistory() {
        try {
            localStorage.setItem('travelSearchHistory', JSON.stringify(searchHistory));
        } catch (e) {
            console.error('Error saving search history:', e);
        }
    }

    function saveCurrentConversation() {
        if (!currentConversationId) return;

        const index = searchHistory.findIndex(c => c.id === currentConversationId);
        if (index !== -1) {
            searchHistory[index].messages = conversationMessages;
            saveSearchHistory();
        }
    }

    function addConversationToHistory(firstMessage) {
        const conversationItem = {
            id: currentConversationId,
            title: firstMessage.length > 50 ? firstMessage.substring(0, 50) + '...' : firstMessage,
            timestamp: new Date().toISOString(),
            messages: [] // Will be populated as we go
        };

        // Add to beginning (most recent first)
        searchHistory.unshift(conversationItem);

        // Limit history to 50 conversations
        if (searchHistory.length > 50) {
            searchHistory = searchHistory.slice(0, 50);
        }

        saveSearchHistory();
        renderHistory();
    }

    function startNewConversation() {
        // Clear current conversation
        chatContainer.innerHTML = '';
        chatContainer.classList.remove('has-messages');
        // Restore welcome message if it was hidden via innerHTML clearing? 
        // Wait, clearing innerHTML remvoes the welcome message div itself!
        // I need to NOT clear the welcome message if I want it back, OR re-inject it.
        // Actually, the welcome message is STATIC in HTML.
        // If I do chatContainer.innerHTML = '', I delete the static welcome message.
        // I should probably Restore it.

        chatContainer.innerHTML = `
            <div class="welcome-message">
                <div class="hero-text">
                    <span class="gradient-text">Hello, Traveler</span>
                </div>
                <p class="subtitle">How can I help you explore the world today?</p>
            </div>
        `;
        currentConversationId = null;
        conversationMessages = [];
        userInput.value = '';
        userInput.focus();

        // Remove active class from history
        document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));
    }

    function loadConversation(id) {
        const conversation = searchHistory.find(c => c.id === id);
        if (!conversation) return;

        currentConversationId = id;
        conversationMessages = conversation.messages || [];

        // Clear and rebuild chat
        chatContainer.innerHTML = `
            <div class="welcome-message">
                <div class="hero-text">
                    <span class="gradient-text">Hello, Traveler</span>
                </div>
                <p class="subtitle">How can I help you explore the world today?</p>
            </div>
        `;
        if (conversationMessages.length > 0) {
            chatContainer.classList.add('has-messages');
        } else {
            chatContainer.classList.remove('has-messages');
        }

        // Replay messages
        conversationMessages.forEach(msg => {
            if (msg.role === 'tool_call_ui') {
                // Reconstruct tool call UI
                const toolDiv = document.createElement('div');
                toolDiv.className = 'tool-call';
                // We don't need ID for history items really

                const displayInfo = msg.displayInfo || getToolDisplayInfo(msg.name, msg.args);

                toolDiv.innerHTML = `
                    <div class="tool-icon">
                        ${displayInfo.icon}
                    </div>
                    <div class="tool-details">
                        <div class="tool-name">${displayInfo.title}</div>
                        <div class="tool-args">${displayInfo.description}</div>
                    </div>
                    <div class="tool-status completed" style="background-color: rgba(34, 197, 94, 0.1); color: #22c55e;">Completed</div>
                `;
                chatContainer.appendChild(toolDiv);
            } else {
                appendMessage(msg.role, msg.content);
            }
        });

        // Remove duplicate messages from state (appendMessage adds them again)
        // Actually appendMessage adds to conversationMessages, so we should reset it before replaying
        // But wait, appendMessage pushes to conversationMessages. 
        // So if we loop and call appendMessage, we are doubling the array.
        // Let's fix this by decoupling UI rendering from state update in appendMessage, 
        // OR just reset conversationMessages after replaying?
        // Better: make appendMessage NOT update state, handle state separately.
        // But for now, let's just reset it to the loaded messages after replaying.
        conversationMessages = conversation.messages || [];

        scrollToBottom();
        renderHistory();
    }

    function deleteConversation(id, event) {
        event.stopPropagation(); // Prevent clicking the item

        showConfirmModal(
            'Delete Conversation',
            'Are you sure you want to delete this conversation?',
            () => {
                searchHistory = searchHistory.filter(c => c.id !== id);
                saveSearchHistory();
                renderHistory();

                if (currentConversationId === id) {
                    startNewConversation();
                }
            }
        );
    }

    function renameConversation(id, newTitle) {
        const conversation = searchHistory.find(c => c.id === id);
        if (conversation) {
            conversation.title = newTitle;
            saveSearchHistory();
            renderHistory();
        }
    }

    function togglePinConversation(id) {
        const conversation = searchHistory.find(c => c.id === id);
        if (conversation) {
            conversation.pinned = !conversation.pinned;
            // Sort: pinned first, then by timestamp
            searchHistory.sort((a, b) => {
                if (a.pinned && !b.pinned) return -1;
                if (!a.pinned && b.pinned) return 1;
                return new Date(b.timestamp) - new Date(a.timestamp);
            });
            saveSearchHistory();
            renderHistory();
        }
    }

    function renderHistory() {
        if (searchHistory.length === 0) {
            historyList.innerHTML = '<div class="history-empty">No search history yet</div>';
            return;
        }

        historyList.innerHTML = '';
        searchHistory.forEach((conversation) => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';

            // Add active class if this is the current conversation
            if (conversation.id === currentConversationId) {
                historyItem.classList.add('active');
            }

            // Add pinned class if pinned
            if (conversation.pinned) {
                historyItem.classList.add('pinned');
            }

            historyItem.innerHTML = `
                <div class="history-item-content">
                    <div class="history-item-text">${escapeHtml(conversation.title)}</div>
                    <div class="history-item-time">${formatTimestamp(conversation.timestamp)}</div>
                </div>
                <div class="history-menu-wrapper">
                    <button class="history-menu-btn" title="Options">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <circle cx="12" cy="5" r="2"/>
                            <circle cx="12" cy="12" r="2"/>
                            <circle cx="12" cy="19" r="2"/>
                        </svg>
                    </button>
                    <div class="history-dropdown hidden">
                        <button class="dropdown-item share-btn">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
                                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
                            </svg>
                            Share conversation
                        </button>
                        <button class="dropdown-item pin-btn">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="12" y1="17" x2="12" y2="22"/>
                                <path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V6h1a2 2 0 0 0 0-4H8a2 2 0 0 0 0 4h1v4.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24Z"/>
                            </svg>
                            ${conversation.pinned ? 'Unpin' : 'Pin'}
                        </button>
                        <button class="dropdown-item rename-btn">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
                            </svg>
                            Rename
                        </button>
                        <button class="dropdown-item delete-btn">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                            </svg>
                            Delete
                        </button>
                    </div>
                </div>
            `;

            // Click on item to load conversation
            historyItem.querySelector('.history-item-content').addEventListener('click', () => {
                loadConversation(conversation.id);
            });

            // 3-dot menu toggle
            const menuBtn = historyItem.querySelector('.history-menu-btn');
            const dropdown = historyItem.querySelector('.history-dropdown');
            menuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                // Close all other dropdowns first
                document.querySelectorAll('.history-dropdown').forEach(d => d.classList.add('hidden'));

                // Position dropdown relative to button
                const rect = menuBtn.getBoundingClientRect();
                dropdown.style.top = `${rect.bottom + 4}px`;
                dropdown.style.left = `${rect.left - 150}px`; // Offset to align right edge

                dropdown.classList.toggle('hidden');
            });

            // Share button
            historyItem.querySelector('.share-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.add('hidden');
                const shareText = `Check out my conversation: ${conversation.title}`;
                if (navigator.share) {
                    navigator.share({ title: conversation.title, text: shareText });
                } else {
                    navigator.clipboard.writeText(shareText);
                    showToast('Copied to clipboard!');
                }
            });

            // Pin button
            historyItem.querySelector('.pin-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.add('hidden');
                togglePinConversation(conversation.id);
            });

            // Rename button
            historyItem.querySelector('.rename-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.add('hidden');
                showInputModal('Rename Conversation', 'Enter new title', conversation.title, (newTitle) => {
                    renameConversation(conversation.id, newTitle);
                });
            });

            // Delete button
            historyItem.querySelector('.delete-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.add('hidden');
                deleteConversation(conversation.id, e);
            });

            historyList.appendChild(historyItem);
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', () => {
            document.querySelectorAll('.history-dropdown').forEach(d => d.classList.add('hidden'));
        });
    }

    function formatTimestamp(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;

        return date.toLocaleDateString();
    }

    function showConfirmModal(title, message, onConfirm) {
        const modal = document.getElementById('confirmation-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalMessage = document.getElementById('modal-message');
        const confirmBtn = document.getElementById('modal-confirm');
        const cancelBtn = document.getElementById('modal-cancel');

        if (!modal) return; // Safety check

        modalTitle.textContent = title;
        modalMessage.textContent = message;

        modal.classList.remove('hidden');
        // Small delay to allow CSS transition
        requestAnimationFrame(() => {
            modal.classList.add('active');
        });

        const cleanup = () => {
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
        };

        const closeModal = () => {
            modal.classList.remove('active');
            setTimeout(() => {
                modal.classList.add('hidden');
            }, 300); // Match CSS transition duration
            cleanup();
        };

        const handleConfirm = () => {
            onConfirm();
            closeModal();
        };

        const handleCancel = () => {
            closeModal();
        };

        // Ensure we don't stack listeners if function called multiple times?
        // We use a cleanup function, but we need to make sure we remove PREVIOUS listeners if any exist?
        // Actually, with the closure, creating new listeners every time is fine IF we cleanup correctly.
        // But what if user clicks outside? 
        // Let's keep it simple: Add listeners, remove on close.
        // To be safe against double-binding if opened rapidly, maybe clone buttons? 
        // No, simple remove is improved by `once: true` if possible, but we need closure access.

        // Better implementation to avoid listener buildup:
        confirmBtn.onclick = handleConfirm;
        cancelBtn.onclick = handleCancel;
    }

    function showInputModal(title, placeholder, defaultValue, onConfirm) {
        const modal = document.getElementById('input-modal');
        const modalTitle = document.getElementById('input-modal-title');
        const inputField = document.getElementById('input-modal-field');
        const confirmBtn = document.getElementById('input-modal-confirm');
        const cancelBtn = document.getElementById('input-modal-cancel');

        if (!modal) return;

        modalTitle.textContent = title;
        inputField.placeholder = placeholder;
        inputField.value = defaultValue || '';

        modal.classList.remove('hidden');
        requestAnimationFrame(() => {
            modal.classList.add('active');
            inputField.focus();
            inputField.select();
        });

        const closeModal = () => {
            modal.classList.remove('active');
            setTimeout(() => {
                modal.classList.add('hidden');
            }, 200);
        };

        const handleConfirm = () => {
            const value = inputField.value.trim();
            if (value) {
                onConfirm(value);
            }
            closeModal();
        };

        const handleCancel = () => {
            closeModal();
        };

        const handleKeydown = (e) => {
            if (e.key === 'Enter') {
                handleConfirm();
            } else if (e.key === 'Escape') {
                handleCancel();
            }
        };

        confirmBtn.onclick = handleConfirm;
        cancelBtn.onclick = handleCancel;
        inputField.onkeydown = handleKeydown;
    }

    function showToast(message) {
        const toast = document.getElementById('toast-notification');
        const toastMessage = document.getElementById('toast-message');

        if (!toast) return;

        toastMessage.textContent = message;
        toast.classList.remove('hidden');

        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Auto-hide after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.classList.add('hidden');
            }, 300);
        }, 3000);
    }

    function escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // ==========================================================================
    // PRD Section 8.3 & 8.4: Trip Workspace & Saved Trips Controllers
    // ==========================================================================

    // Stop Generation Button
    if (stopGenerationBtn) {
        stopGenerationBtn.addEventListener('click', () => {
            if (activeAbortController) {
                activeAbortController.abort();
                activeAbortController = null;
                setProcessing(false);
                showToast('Generation cancelled');
            }
        });
    }

    // Workspace Tab Switching
    const workspaceTabsBar = document.getElementById('workspace-tabs-bar');
    const tabContents = document.querySelectorAll('.tab-content');

    if (workspaceTabsBar) {
        workspaceTabsBar.addEventListener('click', (e) => {
            const btn = e.target.closest('.tab-btn');
            if (!btn) return;
            const targetTab = btn.dataset.tab;

            // Update active button
            workspaceTabsBar.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Switch visible panel
            tabContents.forEach(panel => {
                if (panel.id === `tab-${targetTab}` || (targetTab === 'assistant' && panel.id === 'chat-container')) {
                    panel.classList.remove('hidden');
                    panel.classList.add('active');
                } else {
                    panel.classList.add('hidden');
                    panel.classList.remove('active');
                }
            });

            // If switching to itinerary tab, render active itinerary or load latest from DB
            if (targetTab === 'itinerary') {
                if (currentActiveItinerary) {
                    updateItineraryWorkspace(currentActiveItinerary);
                } else {
                    fetch('/api/trips')
                        .then(r => r.json())
                        .then(data => {
                            if (data.trips && data.trips.length > 0 && !currentActiveItinerary) {
                                fetch(`/api/trips/${data.trips[0].id}`)
                                    .then(r => r.json())
                                    .then(td => {
                                        if (td.trip && td.trip.itinerary_days && td.trip.itinerary_days.length > 0) {
                                            updateItineraryWorkspace(td.trip);
                                        }
                                    });
                            }
                        })
                        .catch(() => {});
                }
            }

            // If switching to saved trips tab, refresh from SQLite
            if (targetTab === 'saved-trips') {
                loadSavedTrips();
            }

            // If switching to LangGraph tab, initialize topology and agents
            if (targetTab === 'langgraph') {
                initLangGraphView();
            }
        });
    }

    // Refresh Saved Trips Button
    const refreshSavedTripsBtn = document.getElementById('refresh-saved-trips-btn');
    if (refreshSavedTripsBtn) {
        refreshSavedTripsBtn.addEventListener('click', () => {
            loadSavedTrips();
            showToast('Trips refreshed');
        });
    }

    // Save Current Itinerary Button
    const saveCurrentItineraryBtn = document.getElementById('save-current-itinerary-btn');
    if (saveCurrentItineraryBtn) {
        saveCurrentItineraryBtn.addEventListener('click', async () => {
            const defaultTitle = currentActiveItinerary ? (currentActiveItinerary.trip_title || currentActiveItinerary.title || `${currentActiveItinerary.destination || 'My'} Trip`) : 'My Planned Trip';
            showInputModal('Save Trip', 'Enter a name for this trip:', async (title) => {
                const tripPayload = {
                    title: title || defaultTitle,
                    origin: (currentActiveItinerary && currentActiveItinerary.origin) || userLocation.airport || 'DEL',
                    destination: (currentActiveItinerary && currentActiveItinerary.destination) || userLocation.city || 'India',
                    duration_days: (currentActiveItinerary && currentActiveItinerary.duration_days) || (currentActiveItinerary && currentActiveItinerary.itinerary_days ? currentActiveItinerary.itinerary_days.length : 4),
                    traveler_count: (currentActiveItinerary && currentActiveItinerary.traveler_count) || 2,
                    budget: (currentActiveItinerary && currentActiveItinerary.budget) || 35000,
                    currency: (currentActiveItinerary && currentActiveItinerary.currency) || userLocation.currency || 'INR',
                    itinerary_days: (currentActiveItinerary && (currentActiveItinerary.itinerary_days || currentActiveItinerary.days)) || [
                        {
                            day_number: 1,
                            title: 'Arrival & Local Exploration',
                            activities: [
                                { time_slot: 'Morning', activity_name: 'Check-in and refresh', location: userLocation.city, duration_minutes: 90, estimated_cost: 0, is_verified: true },
                                { time_slot: 'Afternoon', activity_name: 'City walking tour & market', location: userLocation.city, duration_minutes: 180, estimated_cost: 800, is_verified: false }
                            ]
                        }
                    ]
                };

                try {
                    const res = await fetch('/api/trips', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(tripPayload)
                    });
                    const data = await res.json();
                    if (data.status === 'success') {
                        showToast(`Saved '${data.trip.title}'!`);
                        loadSavedTrips();
                    }
                } catch (e) {
                    console.error('Failed to save trip:', e);
                    showToast('Failed to save trip');
                }
            });
        });
    }

    // Load Saved Trips from SQLite (PRD FR-10)
    async function loadSavedTrips() {
        const container = document.getElementById('saved-trips-container');
        const countBadge = document.getElementById('saved-trips-count');
        if (!container) return;

        try {
            const res = await fetch('/api/trips');
            const data = await res.json();
            const trips = data.trips || [];

            if (countBadge) {
                countBadge.textContent = trips.length;
            }

            if (trips.length === 0) {
                container.innerHTML = `
                    <div class="workspace-empty-state">
                        <div class="empty-icon">📁</div>
                        <h3>No Saved Trips Yet</h3>
                        <p>When you plan a trip in the Travel Assistant, click "Save Trip" to keep it here permanently.</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = trips.map(t => `
                <div class="saved-trip-card" data-trip-id="${t.id}">
                    <div>
                        <h4>${escapeHtml(t.title)}</h4>
                        <div class="saved-trip-route">📍 ${escapeHtml(t.origin)} → ${escapeHtml(t.destination)}</div>
                        <div class="saved-trip-meta">
                            <span>⏳ ${t.duration_days || 1} Days (${t.traveler_count || 1} pax)</span>
                            <span>💰 ${t.currency === 'INR' ? '₹' : t.currency + ' '}${(t.budget || 0).toLocaleString()}</span>
                        </div>
                    </div>
                    <div class="saved-trip-actions">
                        <button type="button" class="btn-primary-sm load-trip-btn" data-trip-id="${t.id}">Open Itinerary</button>
                        <button type="button" class="btn-secondary-sm delete-trip-btn" data-trip-id="${t.id}">Delete</button>
                    </div>
                </div>
            `).join('');

            // Attach action listeners
            container.querySelectorAll('.load-trip-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const tid = btn.dataset.tripId;
                    const tripRes = await fetch(`/api/trips/${tid}`);
                    const tripData = await tripRes.json();
                    if (tripData.status === 'success') {
                        updateItineraryWorkspace(tripData.trip);
                        const itinTabBtn = document.querySelector('[data-tab="itinerary"]');
                        if (itinTabBtn) itinTabBtn.click();
                        appendMessage('user', `Loaded saved trip: "${tripData.trip.title}" (${tripData.trip.origin} → ${tripData.trip.destination})`);
                        appendMessage('assistant', `Loaded trip "${tripData.trip.title}". You have ${tripData.trip.itinerary_days?.length || 0} scheduled days with budget ${tripData.trip.currency === 'INR' ? '₹' : tripData.trip.currency}${tripData.trip.budget?.toLocaleString() || 'N/A'}. View the day-by-day plan in the Itinerary & Timeline tab!`);
                    }
                });
            });

            container.querySelectorAll('.delete-trip-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const tid = btn.dataset.tripId;
                    showConfirmModal('Delete Trip', 'Delete this saved trip permanently?', async () => {
                        await fetch(`/api/trips/${tid}`, { method: 'DELETE' });
                        showToast('Trip deleted');
                        loadSavedTrips();
                    });
                });
            });

        } catch (e) {
            console.error('Failed to load trips:', e);
        }
    }

    // Live Budget Workspace Updater (PRD Section 7)
    function updateBudgetWorkspace(data) {
        if (!data || data.total_cost === undefined) return;

        const currSym = data.currency === 'INR' ? '₹' : (data.currency + ' ');
        const totalEl = document.getElementById('budget-summary-total');
        const splitEl = document.getElementById('budget-summary-split');
        const tableBody = document.getElementById('budget-table-body');
        const targetEl = document.getElementById('budget-target-display');
        const statusBadge = document.getElementById('budget-status-badge');
        const ratioEl = document.getElementById('budget-verified-ratio');
        const progressFill = document.getElementById('budget-progress-fill');
        const tipsList = document.getElementById('savings-tips-list');

        if (totalEl) totalEl.textContent = `${currSym}${data.total_cost.toLocaleString()}`;
        if (splitEl) splitEl.textContent = `${currSym}${data.cost_per_person.toLocaleString()} (${data.traveler_count} pax)`;

        if (data.budget_evaluation) {
            const ev = data.budget_evaluation;
            if (targetEl) {
                targetEl.textContent = ev.target_budget ? `${currSym}${ev.target_budget.toLocaleString()}` : 'Not set';
            }
            if (statusBadge) {
                if (ev.is_over_budget) {
                    statusBadge.textContent = `Over by ${currSym}${ev.overrun_amount.toLocaleString()}`;
                    statusBadge.className = 'status-badge-inline over-budget';
                } else {
                    statusBadge.textContent = 'Within Budget';
                    statusBadge.className = 'status-badge-inline';
                }
            }
            if (progressFill && ev.utilization_pct) {
                progressFill.style.width = `${Math.min(100, ev.utilization_pct)}%`;
                progressFill.style.backgroundColor = ev.is_over_budget ? '#ef4444' : '#3b82f6';
            }
            if (tipsList && ev.savings_suggestions && ev.savings_suggestions.length > 0) {
                tipsList.innerHTML = ev.savings_suggestions.map(s => `<li>${escapeHtml(s)}</li>`).join('');
            }
        }

        if (data.verification_audit && ratioEl) {
            ratioEl.textContent = `${data.verification_audit.verified_ratio_pct}% verified`;
        }

        // Populate itemized rows
        if (tableBody && data.itemized_items) {
            const rows = [];
            for (const [cat, items] of Object.entries(data.itemized_items)) {
                if (items && items.length > 0) {
                    items.forEach(item => {
                        const isVer = item.is_verified;
                        rows.push(`
                            <tr>
                                <td><strong>${escapeHtml(cat.replace('_', ' ').toUpperCase())}</strong></td>
                                <td>${escapeHtml(item.description)}</td>
                                <td>${currSym}${item.amount.toLocaleString()}</td>
                                <td><span class="${isVer ? 'verified-tag' : 'estimate-tag'}">${isVer ? 'Verified' : 'Estimate'}</span></td>
                            </tr>
                        `);
                    });
                }
            }
            if (rows.length > 0) {
                tableBody.innerHTML = rows.join('');
            }
        }
    }

    // Flights Workspace Updater
    function updateFlightsWorkspace(data) {
        const list = document.getElementById('flights-cards-list');
        if (!list) return;
        const flights = data.flights || (Array.isArray(data) ? data : []);
        if (flights.length === 0) return;

        list.innerHTML = flights.map(f => {
            const isRoundTrip = f.trip_type === 'round_trip' || !!f.return_time || !!f.return_flight;
            const tripBadge = isRoundTrip ? '<span class="status-badge-inline" style="margin-left:6px;font-size:0.75rem;">Round-Trip</span>' : '';
            const paxInfo = f.passengers && f.passengers > 1 ? ` (${f.passengers} pax)` : '';
            const routeStr = isRoundTrip 
                ? `🛫 ${escapeHtml(f.origin || '')} ⇄ ${escapeHtml(f.destination || '')} | Out: ${escapeHtml(f.departure_time || '')} • Ret: ${escapeHtml(f.return_time || (f.return_flight && f.return_flight.departure_time) || '')}`
                : `🕒 ${escapeHtml(f.departure_time || 'Morning')} | ${escapeHtml(f.origin || '')} → ${escapeHtml(f.destination || '')}`;

            return `
            <div class="flight-deal-card">
                <div class="deal-header">
                    <span class="deal-carrier">✈️ ${escapeHtml(f.airline || f.carrier || 'Airline')} (${escapeHtml(f.flight_id || '')}) ${tripBadge}</span>
                    <span class="deal-price">${f.currency === 'INR' ? '₹' : (f.currency || '₹') + ' '}${(f.price || 0).toLocaleString()}${paxInfo}</span>
                </div>
                <div class="deal-meta">
                    ${routeStr}
                </div>
                ${f.booking_url ? `<a href="${f.booking_url}" target="_blank" rel="noopener" class="deal-book-btn">Book on Aviasales</a>` : ''}
            </div>
            `;
        }).join('');
    }

    // Hotels Workspace Updater
    function updateHotelsWorkspace(data) {
        const list = document.getElementById('hotels-cards-list');
        if (!list) return;
        const hotels = data.hotels || data.offers || (Array.isArray(data) ? data : []);
        if (hotels.length === 0) return;

        list.innerHTML = hotels.map(h => `
            <div class="hotel-deal-card">
                <div class="deal-header">
                    <span class="deal-carrier">🏨 ${escapeHtml(h.name || h.hotel_name || 'Hotel Stay')}</span>
                    <span class="deal-price">${h.currency === 'INR' ? '₹' : (h.currency || '₹') + ' '}${(h.price || h.rate || 0).toLocaleString()}</span>
                </div>
                <div class="deal-meta">
                    📍 ${escapeHtml(h.location || h.city_code || 'City Center')} | ⭐ ${h.rating || '4.0'}
                </div>
                ${h.booking_url ? `<a href="${h.booking_url}" target="_blank" rel="noopener" class="deal-book-btn">View on Hotellook</a>` : ''}
            </div>
        `).join('');
    }

    // Live Itinerary Workspace Updater (PRD Section 6 & FR-04)
    function updateItineraryWorkspace(data) {
        if (!data) return;
        const container = document.getElementById('itinerary-timeline-container');
        if (!container) return;

        const days = data.itinerary_days || data.days || [];
        if (!Array.isArray(days) || days.length === 0) return;

        currentActiveItinerary = data;

        // Update Itinerary Tab badge
        const itinBadge = document.getElementById('itinerary-badge');
        if (itinBadge) {
            itinBadge.textContent = `${days.length} Day${days.length > 1 ? 's' : ''}`;
            itinBadge.classList.remove('hidden');
        }

        const currSym = (data.currency === 'INR' || !data.currency) ? '₹' : `${data.currency} `;

        container.innerHTML = days.map(d => {
            const dayNum = d.day_number || 1;
            const dayTitle = d.title || `Day ${dayNum}`;
            const dateStr = d.date ? `<span class="activity-time-pill">📅 ${escapeHtml(d.date)}</span>` : '';
            const activities = d.activities || [];

            const activitiesHtml = activities.length > 0 ? activities.map(a => {
                const timeSlot = a.time_slot || 'Activity';
                const name = a.activity_name || a.name || 'Sightseeing';
                const loc = a.location ? `📍 ${escapeHtml(a.location)}` : '';
                const dur = a.duration_minutes ? `⏳ ${a.duration_minutes} mins` : '';
                const costVal = (a.estimated_cost !== undefined && a.estimated_cost > 0) ? `💰 ${currSym}${Number(a.estimated_cost).toLocaleString()}` : '';
                const notes = a.notes ? `💡 ${escapeHtml(a.notes)}` : '';

                const metaParts = [loc, dur, costVal, notes].filter(Boolean).join(' • ');

                return `
                    <div class="timeline-activity-item">
                        <span class="activity-time-pill">${escapeHtml(timeSlot)}</span>
                        <div class="activity-details-col">
                            <div class="activity-name">${escapeHtml(name)}</div>
                            ${metaParts ? `<div class="activity-meta">${metaParts}</div>` : ''}
                        </div>
                    </div>
                `;
            }).join('') : `
                <div class="timeline-activity-item">
                    <span class="activity-time-pill">All Day</span>
                    <div class="activity-details-col">
                        <div class="activity-name">${escapeHtml(d.day_notes || 'Leisure and exploration')}</div>
                    </div>
                </div>
            `;

            return `
                <div class="timeline-day-card">
                    <div class="timeline-day-header">
                        <div class="timeline-day-title">Day ${dayNum}: ${escapeHtml(dayTitle.replace(/^Day \d+[:\s-]*/i, ''))}</div>
                        ${dateStr}
                    </div>
                    <div class="timeline-day-activities">
                        ${activitiesHtml}
                    </div>
                </div>
            `;
        }).join('');
    }

    // Fallback parser to extract day plans from assistant conversation text
    function parseItineraryFromText(text) {
        if (!text || typeof text !== 'string') return;
        const dayRegex = /(?:###?\s*)?(?:Day\s*(\d+)|\b(\d+)\.\s*Day\s*\d+)[:\s–—-]+([^\n]+)/gi;
        const matches = [...text.matchAll(dayRegex)];
        if (matches.length < 2) return;

        const days = [];
        for (let i = 0; i < matches.length; i++) {
            const match = matches[i];
            const dayNum = parseInt(match[1] || match[2] || (i + 1), 10);
            const title = match[3].trim().replace(/\*\*/g, '');
            const startIndex = match.index + match[0].length;
            const endIndex = (i + 1 < matches.length) ? matches[i + 1].index : text.length;
            const dayBody = text.slice(startIndex, endIndex);

            const lines = dayBody.split('\n')
                .map(l => l.trim())
                .filter(l => l && (l.startsWith('-') || l.startsWith('*') || /^\d+\./.test(l) || l.includes(':')));

            const activities = [];
            for (const line of lines) {
                const clean = line.replace(/^[-*•\d.]+\s*/, '').replace(/\*\*/g, '').trim();
                if (!clean) continue;
                
                const colonIdx = clean.indexOf(':');
                let slot = 'Activity';
                let actName = clean;
                if (colonIdx > 0 && colonIdx < 20) {
                    slot = clean.substring(0, colonIdx).trim();
                    actName = clean.substring(colonIdx + 1).trim();
                }

                activities.push({
                    time_slot: slot,
                    activity_name: actName,
                    location: '',
                    duration_minutes: 120,
                    estimated_cost: 0,
                    is_verified: false
                });
            }

            days.push({
                day_number: dayNum,
                title: title || `Day ${dayNum} Plan`,
                activities: activities.length > 0 ? activities : [
                    { time_slot: 'All Day', activity_name: title, location: '', duration_minutes: 240, estimated_cost: 0 }
                ]
            });
        }

        if (days.length > 0) {
            updateItineraryWorkspace({
                destination: userLocation.city || 'Your Destination',
                duration_days: days.length,
                traveler_count: 2,
                currency: userLocation.currency || 'INR',
                itinerary_days: days
            });
        }
    }

    // Initial load of saved trips count and latest itinerary
    loadSavedTrips();
    fetch('/api/trips')
        .then(r => r.json())
        .then(data => {
            if (data.trips && data.trips.length > 0 && !currentActiveItinerary) {
                fetch(`/api/trips/${data.trips[0].id}`)
                    .then(r => r.json())
                    .then(td => {
                        if (td.trip && td.trip.itinerary_days && td.trip.itinerary_days.length > 0) {
                            updateItineraryWorkspace(td.trip);
                        }
                    });
            }
        })
        .catch(() => {});

    // =========================================================================
    // LANGGRAPH MULTI-AGENT MESH & DEMONSTRATION ENGINE
    // =========================================================================

    const sidebarViewLangGraphBtn = document.getElementById('sidebar-view-langgraph-btn');
    if (sidebarViewLangGraphBtn) {
        sidebarViewLangGraphBtn.addEventListener('click', () => {
            const tabBtn = document.querySelector('.tab-btn[data-tab="langgraph"]');
            if (tabBtn) {
                tabBtn.click();
            }
        });
    }

    let graphTopologyCache = null;
    let agentsCache = null;
    let isDemoRunning = false;
    let activeDemoTimer = null;
    let demoStepIndex = 0;
    let demoTraceData = [];

    // LangGraph Subview Switching
    const subnavButtons = document.querySelectorAll('.langgraph-subnav-btn');
    const langgraphSubviews = document.querySelectorAll('.langgraph-subview');
    subnavButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const subview = btn.dataset.subview;
            subnavButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            langgraphSubviews.forEach(view => {
                if (view.id === `subview-${subview}`) {
                    view.classList.remove('hidden');
                    view.classList.add('active');
                } else {
                    view.classList.add('hidden');
                    view.classList.remove('active');
                }
            });
        });
    });

    // Inspector close button
    const closeInspectorBtn = document.getElementById('close-inspector-btn');
    const nodeInspectorDrawer = document.getElementById('node-inspector-drawer');
    if (closeInspectorBtn && nodeInspectorDrawer) {
        closeInspectorBtn.addEventListener('click', () => {
            nodeInspectorDrawer.classList.add('hidden');
        });
    }

    // Node Coordinates for SVG Rendering
    const NODE_COORDINATES = {
        '__start__': { x: 30, y: 220, w: 120, h: 60, rx: 8 },
        'supervisor': { x: 180, y: 200, w: 180, h: 90, rx: 12 },
        'flight_specialist': { x: 420, y: 35, w: 185, h: 72, rx: 10 },
        'hotel_specialist': { x: 420, y: 135, w: 185, h: 72, rx: 10 },
        'local_guide_specialist': { x: 420, y: 235, w: 185, h: 72, rx: 10 },
        'feasibility_validator': { x: 420, y: 335, w: 185, h: 72, rx: 10 },
        'itinerary_builder': { x: 670, y: 125, w: 185, h: 78, rx: 10 },
        'budget_auditor': { x: 670, y: 285, w: 185, h: 78, rx: 10 },
        'payment_agent': { x: 800, y: 285, w: 135, h: 60, rx: 8 },
        '__end__': { x: 855, y: 180, w: 90, h: 58, rx: 8 },
    };

    function createCurvedPath(x1, y1, x2, y2) {
        const dx = (x2 - x1) * 0.5;
        return `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
    }

    async function initLangGraphView() {
        try {
            const [topRes, agentsRes] = await Promise.all([
                fetch('/api/graph/topology'),
                fetch('/api/agents')
            ]);
            const topData = await topRes.json();
            const agentsData = await agentsRes.json();

            if (topData.topology) {
                graphTopologyCache = topData.topology;
                renderGraphTopology(topData.topology);
                renderStateChannels(topData.topology.state_channels);
            }
            if (agentsData.agents) {
                agentsCache = agentsData.agents;
                renderAgentCards(agentsData.agents);
                const countDisp = document.getElementById('agent-count-display');
                if (countDisp) countDisp.textContent = agentsData.agents.length;
            }
        } catch (e) {
            console.error('Failed to initialize LangGraph view', e);
        }
    }

    function renderGraphTopology(topology) {
        const svgEdgesGroup = document.getElementById('svg-edges-group');
        const svgNodesGroup = document.getElementById('svg-nodes-group');
        if (!svgEdgesGroup || !svgNodesGroup) return;

        svgEdgesGroup.innerHTML = '';
        svgNodesGroup.innerHTML = '';

        // Render Edges
        topology.edges.forEach(edge => {
            const srcCoord = NODE_COORDINATES[edge.from_node];
            const dstCoord = NODE_COORDINATES[edge.to_node];
            if (!srcCoord || !dstCoord) return;

            const x1 = srcCoord.x + srcCoord.w;
            const y1 = srcCoord.y + srcCoord.h / 2;
            const x2 = dstCoord.x;
            const y2 = dstCoord.y + dstCoord.h / 2;

            const d = createCurvedPath(x1, y1, x2, y2);
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', d);
            path.setAttribute('class', 'svg-edge-path');
            path.setAttribute('id', `edge-${edge.from_node}-${edge.to_node}`);
            path.setAttribute('marker-end', 'url(#arrowhead)');
            svgEdgesGroup.appendChild(path);

            if (edge.label && Math.abs(x2 - x1) > 80) {
                const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                label.setAttribute('x', (x1 + x2) / 2);
                label.setAttribute('y', (y1 + y2) / 2 - 6);
                label.setAttribute('class', 'svg-edge-label');
                label.textContent = edge.label;
                svgEdgesGroup.appendChild(label);
            }
        });

        // Render Nodes
        topology.nodes.forEach(node => {
            const coord = NODE_COORDINATES[node.id];
            if (!coord) return;

            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.setAttribute('class', `svg-node-group ${node.enabled === false ? 'disabled' : ''}`);
            g.setAttribute('id', `node-${node.id}`);
            g.setAttribute('transform', `translate(${coord.x}, ${coord.y})`);

            // Node Background Rect
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('width', coord.w);
            rect.setAttribute('height', coord.h);
            rect.setAttribute('rx', coord.rx || 10);
            rect.setAttribute('ry', coord.rx || 10);
            rect.setAttribute('class', 'svg-node-rect');
            if (node.id === '__start__' || node.id === '__end__') {
                rect.style.fill = '#1e293b';
                rect.style.stroke = '#475569';
            } else if (node.color) {
                rect.style.borderColor = node.color;
            }
            g.appendChild(rect);

            // Node Icon
            const iconText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            iconText.setAttribute('x', 14);
            iconText.setAttribute('y', coord.h / 2 + 7);
            iconText.setAttribute('font-size', '20px');
            iconText.textContent = node.icon || '🤖';
            g.appendChild(iconText);

            // Node Title
            const titleText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            titleText.setAttribute('x', 44);
            titleText.setAttribute('y', coord.h > 65 ? 26 : 24);
            titleText.setAttribute('class', 'svg-node-title');
            titleText.textContent = truncate(node.name || node.id, coord.w > 150 ? 18 : 12);
            g.appendChild(titleText);

            // Node Role / Subtitle
            const roleText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            roleText.setAttribute('x', 44);
            roleText.setAttribute('y', coord.h > 65 ? 42 : 38);
            roleText.setAttribute('class', 'svg-node-subtitle');
            roleText.textContent = truncate(node.role || 'Agent', coord.w > 150 ? 22 : 14);
            g.appendChild(roleText);

            // Node Badge
            if (coord.h > 65) {
                const badgeText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                badgeText.setAttribute('x', 44);
                badgeText.setAttribute('y', 58);
                badgeText.setAttribute('class', 'svg-node-badge');
                if (node.color) badgeText.setAttribute('fill', node.color);
                badgeText.textContent = (node.badge || 'Domain Worker').toUpperCase();
                g.appendChild(badgeText);
            }

            // Click listener -> Open Inspector
            g.addEventListener('click', () => {
                inspectAgentNode(node);
            });

            svgNodesGroup.appendChild(g);
        });
    }

    function truncate(str, maxLen) {
        if (!str) return '';
        return str.length > maxLen ? str.slice(0, maxLen - 1) + '…' : str;
    }

    function inspectAgentNode(node) {
        if (!nodeInspectorDrawer) return;
        nodeInspectorDrawer.classList.remove('hidden');

        const titleEl = document.getElementById('inspector-title');
        const iconEl = document.getElementById('inspector-icon');
        const bodyEl = document.getElementById('inspector-body');

        if (titleEl) titleEl.textContent = node.name || node.id;
        if (iconEl) iconEl.textContent = node.icon || '🤖';

        const toolsList = (node.tools && node.tools.length > 0)
            ? node.tools.map(t => `<span class="inspector-tool-tag">${t}</span>`).join('')
            : '<span class="text-muted">No external tools (Pure reasoning / orchestrator)</span>';

        bodyEl.innerHTML = `
            <div class="inspector-meta-row">
                <span class="inspector-badge-pill">Role: ${node.role || 'Domain Worker'}</span>
                <span class="inspector-badge-pill">Status: <strong>${node.status || 'Active'}</strong></span>
                <span class="inspector-badge-pill">Model: ${node.model || 'gemini-2.5-flash'}</span>
                <span class="inspector-badge-pill">Avg Latency: ${node.avg_latency_ms || 320}ms</span>
            </div>
            <p style="font-size: 0.82rem; color: #334155; margin-bottom: 0.75rem; line-height: 1.45;">
                ${node.description || 'Executes specialized domain subtasks within the LangGraph multi-agent state graph.'}
            </p>
            <div style="margin-bottom: 0.75rem;">
                <strong style="font-size: 0.75rem; text-transform: uppercase; color: #64748b;">Mounted MCP Tools (${(node.tools || []).length}):</strong>
                <div class="inspector-tools-list">${toolsList}</div>
            </div>
            <button type="button" class="btn-test-agent" style="margin-top: 0.5rem;" onclick="window.testAgentQuick('${node.id}')">
                ⚡ Dispatch Test Query to ${node.name || node.id}
            </button>
        `;
    }

    window.testAgentQuick = function(agentId) {
        testAgentInIsolation(agentId);
    };

    function renderAgentCards(agents) {
        const grid = document.getElementById('agent-management-grid');
        if (!grid) return;

        grid.innerHTML = agents.map(agent => {
            const isChecked = agent.enabled !== false ? 'checked' : '';
            const toolsList = agent.tools && agent.tools.length > 0
                ? agent.tools.map(t => `<span class="inspector-tool-tag">${t}</span>`).join(' ')
                : '<span style="font-size:0.75rem; color:#94a3b8;">No direct tools</span>';

            return `
                <div class="agent-manage-card ${agent.enabled === false ? 'disabled' : ''}" id="manage-card-${agent.id}">
                    <div>
                        <div class="card-top-row">
                            <div class="card-agent-identity">
                                <span class="card-agent-icon">${agent.icon || '🤖'}</span>
                                <div class="card-agent-names">
                                    <h4>${agent.name}</h4>
                                    <span>${agent.role}</span>
                                </div>
                            </div>
                            <label class="switch" title="Toggle Agent On/Off">
                                <input type="checkbox" ${isChecked} onchange="window.handleAgentToggle('${agent.id}', this.checked)">
                                <span class="slider"></span>
                            </label>
                        </div>
                        <p class="card-description">${agent.description}</p>
                    </div>

                    <div>
                        <div class="card-form-grid">
                            <div class="card-form-group">
                                <label>Model Override</label>
                                <select class="card-form-select" onchange="window.handleAgentModel('${agent.id}', this.value)">
                                    <option value="gemini-2.5-flash" ${agent.model === 'gemini-2.5-flash' ? 'selected' : ''}>gemini-2.5-flash</option>
                                    <option value="gpt-4o" ${agent.model === 'gpt-4o' ? 'selected' : ''}>gpt-4o</option>
                                    <option value="claude-3-5-sonnet" ${agent.model === 'claude-3-5-sonnet' ? 'selected' : ''}>claude-3.5-sonnet</option>
                                </select>
                            </div>
                            <div class="card-form-group">
                                <label>Temp: <span id="temp-val-${agent.id}">${agent.temperature || 0.2}</span></label>
                                <input type="range" class="card-temp-slider" min="0" max="1" step="0.1" value="${agent.temperature || 0.2}"
                                    oninput="document.getElementById('temp-val-${agent.id}').textContent=this.value"
                                    onchange="window.handleAgentTemp('${agent.id}', this.value)">
                            </div>
                        </div>

                        <div class="card-tools-section">
                            <div class="card-tools-title">Bound MCP Tools (${(agent.tools || []).length})</div>
                            <div class="inspector-tools-list">${toolsList}</div>
                        </div>

                        <div class="card-metrics-row">
                            <span>Invocations: <strong>${agent.calls_count || 12}</strong></span>
                            <span>Avg Latency: <strong>${agent.avg_latency_ms || 320}ms</strong></span>
                            <span>Success: <strong style="color: #16a34a;">100%</strong></span>
                        </div>

                        <button type="button" class="btn-test-agent" onclick="window.testAgentQuick('${agent.id}')">
                            Test ${agent.name} in Isolation
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    window.handleAgentToggle = async function(agentId, enabled) {
        try {
            await fetch(`/api/agents/${agentId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled })
            });
            const card = document.getElementById(`manage-card-${agentId}`);
            if (card) {
                if (enabled) card.classList.remove('disabled');
                else card.classList.add('disabled');
            }
            const nodeEl = document.getElementById(`node-${agentId}`);
            if (nodeEl) {
                if (enabled) nodeEl.classList.remove('disabled');
                else nodeEl.classList.add('disabled');
            }
            showToast(`${agentId} is now ${enabled ? 'Enabled' : 'Disabled'}`);
        } catch (e) {
            console.error('Error toggling agent', e);
        }
    };

    window.handleAgentModel = async function(agentId, model) {
        try {
            await fetch(`/api/agents/${agentId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model })
            });
            showToast(`Updated ${agentId} model to ${model}`);
        } catch (e) {
            console.error('Error setting model', e);
        }
    };

    window.handleAgentTemp = async function(agentId, temperature) {
        try {
            await fetch(`/api/agents/${agentId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ temperature: parseFloat(temperature) })
            });
        } catch (e) {
            console.error('Error setting temp', e);
        }
    };

    async function testAgentInIsolation(agentId) {
        try {
            showToast(`Testing ${agentId}...`);
            const res = await fetch(`/api/agents/${agentId}/test`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: 'Execute isolated unit test' })
            });
            const data = await res.json();
            if (data.status === 'success') {
                showToast(`✓ ${data.agent_name}: Response received!`);
                // Highlight node
                const nodeEl = document.getElementById(`node-${agentId}`);
                if (nodeEl) {
                    nodeEl.classList.add('active');
                    setTimeout(() => nodeEl.classList.remove('active'), 1500);
                }
            }
        } catch (e) {
            console.error('Failed to test agent', e);
        }
    }

    function renderStateChannels(channels) {
        const grid = document.getElementById('channels-grid');
        if (!grid || !channels) return;

        grid.innerHTML = channels.map(ch => `
            <div class="channel-card">
                <div class="channel-name">${ch.channel}</div>
                <div class="channel-type">${ch.type}</div>
                <div class="channel-desc">${ch.description}</div>
            </div>
        `).join('');
    }

    // Live Demonstration Execution
    const runDemoBtn = document.getElementById('run-demo-btn');
    const resetDemoBtn = document.getElementById('reset-demo-btn');
    const demoScenarioSelect = document.getElementById('demo-scenario-select');
    const currentStepBadge = document.getElementById('current-step-badge');
    const consoleStreamLog = document.getElementById('console-stream-log');
    const graphStatusText = document.getElementById('graph-status-text');

    if (runDemoBtn) {
        runDemoBtn.addEventListener('click', () => {
            if (isDemoRunning) return;
            runLangGraphDemonstration();
        });
    }

    if (resetDemoBtn) {
        resetDemoBtn.addEventListener('click', () => {
            resetLangGraphDemonstration();
        });
    }

    async function runLangGraphDemonstration() {
        const scenarioId = (demoScenarioSelect && demoScenarioSelect.value) || 'goa_4day';
        isDemoRunning = true;
        if (runDemoBtn) {
            runDemoBtn.classList.add('running');
            const label = document.getElementById('demo-btn-label');
            if (label) label.textContent = 'Running Demo...';
        }
        if (graphStatusText) graphStatusText.textContent = 'State: Demonstrating Graph Traversal';

        // Clear previous logs
        if (consoleStreamLog) consoleStreamLog.innerHTML = '';
        clearGraphHighlights();

        try {
            const res = await fetch('/api/graph/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scenario_id: scenarioId })
            });
            const data = await res.json();
            demoTraceData = data.trace || [];
            demoStepIndex = 0;

            playNextDemoStep();
        } catch (e) {
            console.error('Simulation failed', e);
            isDemoRunning = false;
            if (runDemoBtn) {
                runDemoBtn.classList.remove('running');
                const label = document.getElementById('demo-btn-label');
                if (label) label.textContent = 'Run Live Demo';
            }
        }
    }

    function playNextDemoStep() {
        if (demoStepIndex >= demoTraceData.length) {
            // Completed
            isDemoRunning = false;
            if (runDemoBtn) {
                runDemoBtn.classList.remove('running');
                const label = document.getElementById('demo-btn-label');
                if (label) label.textContent = 'Run Live Demo';
            }
            if (graphStatusText) graphStatusText.textContent = 'State: Demonstration Complete (All Nodes Executed)';
            showToast('✓ LangGraph Multi-Agent Demonstration Complete');
            return;
        }

        const step = demoTraceData[demoStepIndex];
        demoStepIndex++;

        // Update step badge
        if (currentStepBadge) {
            currentStepBadge.textContent = `Step: ${step.step} / ${demoTraceData.length}`;
        }

        // Highlight SVG Edge
        if (step.active_edge) {
            const edgeEl = document.getElementById(`edge-${step.active_edge.from}-${step.active_edge.to}`);
            if (edgeEl) {
                edgeEl.classList.add('active');
            }
        }

        // Highlight Node
        if (step.agent_id) {
            const nodeEl = document.getElementById(`node-${step.agent_id}`);
            if (nodeEl) {
                nodeEl.classList.add('active');
            }
        }

        // Append Step Card into console stream
        if (consoleStreamLog) {
            const stepDiv = document.createElement('div');
            stepDiv.className = 'step-log-item active';
            stepDiv.innerHTML = `
                <div class="step-item-header">
                    <div class="step-agent-info">
                        <span>🤖</span>
                        <span>${step.agent_id.replace('_', ' ').toUpperCase()}</span>
                    </div>
                    <span class="step-number-tag">Step ${step.step} / ${demoTraceData.length}</span>
                </div>
                <div class="step-action-title">${step.action}</div>
                <div class="step-detail-text">${step.detail}</div>
                <div class="step-payload-preview">State: ${JSON.stringify(step.state_update)}</div>
            `;
            consoleStreamLog.appendChild(stepDiv);
            consoleStreamLog.scrollTop = consoleStreamLog.scrollHeight;
        }

        // Schedule next step
        activeDemoTimer = setTimeout(() => {
            // Demote active to completed
            if (step.agent_id) {
                const nodeEl = document.getElementById(`node-${step.agent_id}`);
                if (nodeEl) {
                    nodeEl.classList.remove('active');
                    nodeEl.classList.add('completed');
                }
            }
            playNextDemoStep();
        }, 750);
    }

    function clearGraphHighlights() {
        document.querySelectorAll('.svg-node-group').forEach(el => {
            el.classList.remove('active', 'completed');
        });
        document.querySelectorAll('.svg-edge-path').forEach(el => {
            el.classList.remove('active');
        });
    }

    function resetLangGraphDemonstration() {
        if (activeDemoTimer) clearTimeout(activeDemoTimer);
        isDemoRunning = false;
        demoStepIndex = 0;
        clearGraphHighlights();
        if (runDemoBtn) {
            runDemoBtn.classList.remove('running');
            const label = document.getElementById('demo-btn-label');
            if (label) label.textContent = 'Run Live Demo';
        }
        if (currentStepBadge) currentStepBadge.textContent = 'Step: 0 / 8';
        if (graphStatusText) graphStatusText.textContent = 'State: Standby / Ready';
        if (consoleStreamLog) {
            consoleStreamLog.innerHTML = `
                <div class="console-welcome">
                    <div class="welcome-icon">🎬</div>
                    <h4>Multi-Agent Demonstration Ready</h4>
                    <p>Select a scenario above and click <strong>"Run Live Demo"</strong> to watch the supervisor, flight specialist, local guide, itinerary planner, and budget auditor collaborate in real-time!</p>
                </div>
            `;
        }
        showToast('LangGraph state reset');
    }

    // Highlight agent during real chat tool executions
    function highlightAgentByTool(toolName, _args) {
        let agentId = 'supervisor';
        if (toolName.includes('flight')) agentId = 'flight_specialist';
        else if (toolName.includes('hotel')) agentId = 'hotel_specialist';
        else if (toolName.includes('itinerary')) agentId = 'itinerary_builder';
        else if (toolName.includes('budget')) agentId = 'budget_auditor';
        else if (toolName.includes('feasibility')) agentId = 'feasibility_validator';
        else if (toolName.includes('guide')) agentId = 'local_guide_specialist';
        else if (toolName.includes('payment')) agentId = 'payment_agent';

        const nodeEl = document.getElementById(`node-${agentId}`);
        if (nodeEl) {
            nodeEl.classList.add('active');
            setTimeout(() => {
                nodeEl.classList.remove('active');
                nodeEl.classList.add('completed');
            }, 1200);
        }
    }
});


