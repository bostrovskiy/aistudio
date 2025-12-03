


    "use strict";
window.SnapInChatLibrary = SnapInChatLibrary;

/**
 * 
 * @param {{
 *      targetElement: HTMLDivElement;
 *      displayHelpButton?: boolean;
 *      handleChatNotSupported: () => void;
 *      onChatReady?: () => void;
 *      onChatButtonReady?: () => void;
 *      onChatOpen?: () => void;
 *      onChatClose?: () => void;
 * }} options 
 * @returns {openChat: () => void }
 */
function SnapInChatLibrary(options) {
    var SALESFORCE_DOMAIN = 'https://service.force.com';
    var BH_SALESFORCE_DOMAIN = 'https://bnh.my.salesforce-sites.com/';
    var BH_MYSALESFORCE_DOMAIN = 'https://bnh.my.salesforce.com';
    var SALESFORCE_ORG_ID = '00D1a000000K8nw';
    var SALESFORCE_LIVEAGENT_CONTENT_URL = 'https://c.la11-core1.sfdc-8tgtt5.salesforceliveagent.com/content';
    var SALESFORCE_LIVEAGENT_CHAT_URL = 'https://d.la11-core1.sfdc-8tgtt5.salesforceliveagent.com/chat';
    var SNAPINS_DEPLOYMENT_ID = '5721a000000Cfej';
    var SNAPINS_BUTTON_ID = '5732L00000005mQ';
    var SNAPINS_DEPLOYMENT_NAME = 'Snap_Ins';
    
    var QUEUE_IDS = {
        PRIMARY: {
            technicalQuestion: 'a0i1a000001O6L1AAK',
        },
        SECONDARY: {
            proVideoV: 'a0i2L000004Fhg8QAC',
            proAudioV: 'a0i2L000004FhgDQAS',
            lightingV: 'a0i2L000004FhgIQAS',
            photoV:    'a0i2L000004FhgSQAS',
            homeEntertainment:    'a0i1a000001O6LDAA0'
        }
    };
    
    var IFRAME_SET_ATTRIBUTE_NAME = "data-has-iframe";

    var chatQueue = null; // passed via openChat(options)

    var openChatOnLoad = false;
    var chatReady = false;

    _loadChat();

    window.addEventListener("message", function (e) {
        if (e.data === 'snapInsNotSupported') {
            options.handleChatNotSupported();
            embedded_svc.hideHelpButton();
        }
    }, false);

    function initESW(gslbBaseURL) {
        var targetElement = options.targetElement;
        var displayHelpButton = options.displayHelpButton;

        window.addEventListener("message", function (payload) {
            if (payload.data === "clearActiveChatSessions") {
                embedded_svc.postMessage("chasitor.decrementActiveChatSession");
            }
        });

        embedded_svc.addEventHandler("onSettingsCallCompleted", function(data) {
            chatReady = true;

            if (openChatOnLoad) {
                openChat({chatQueue: chatQueue});
            }
            
            if(options.onChatReady){
                options.onChatReady();
            }
        });

        var sfButtonReady = false;
        var observer = new MutationObserver(function () {
            if (!sfButtonReady && options.onChatButtonReady && targetElement.querySelector(".embeddedServiceHelpButton")) {
                sfButtonReady = true;
                options.onChatButtonReady();
            }
        });
        observer.observe(targetElement, { childList: true, subtree: true });
        embedded_svc.settings.targetElement = targetElement;
        embedded_svc.settings.displayHelpButton = displayHelpButton;
        embedded_svc.settings.autoOpenPostChat = true;
        embedded_svc.settings.defaultMinimizedText = 'Chat'; //(Defaults to Chat with an Expert)
        embedded_svc.settings.disabledMinimizedText = 'Chat'; //(Defaults to Agent Offline)
        embedded_svc.settings.offlineSupportMinimizedText = 'Chat'; //(Defaults to Contact Us)
        embedded_svc.settings.enabledFeatures = ['LiveAgent'];
        embedded_svc.settings.entryFeature = 'LiveAgent';
        embedded_svc.settings.storageDomain = 'bhphotovideo.com'; //(Sets the domain for your deployment so that visitors can navigate subdomains during a chat session)

        /* 
         * Added as instructed by Salesforce, fixes chat breaking as user navigates quickly from page to page.
         * The fix breaks safari, so as per Salesforce we're temporarily not enabling it for safari until they fix it.
         */
        var isSafari = window.safari !== undefined;
        embedded_svc.settings.__synchronous_decrement_tab = !isSafari;

        embedded_svc.settings.directToButtonRouting = function (prechatFormData) {
			// Dynamically changes the button ID based on what the visitor enters in the pre-chat form.
			// Returns a valid button ID.
			if (prechatFormData.length > 0)	{
				sessionStorage.setItem("ESW_BUTTON_ID", JSON.stringify(prechatFormData));
                return prechatFormData[4]['value'];
			}
			var data = JSON.parse(sessionStorage.getItem("ESW_BUTTON_ID"));
			return data[4]['value'];
		};
	    
	    embedded_svc.settings.extraPrechatInfo = [
			{
				"entityName": "Contact",
				"entityFieldMaps": [
					{"doCreate": false, "doFind": false, "fieldName": "LastName", "isExactMatch": true, "label": "Last Name" },
					{"doCreate": false, "doFind": false, "fieldName": "FirstName", "isExactMatch": true, "label": "First Name" },
					{"doCreate": false, "doFind": false, "fieldName": "Email", "isExactMatch": true, "label": "Email", "displayToAgent": false }
				]
			},
			{
				"entityName": "Case",
				"showOnCreate": true,
				"saveToTranscript": "CaseId",
				"entityFieldMaps": [
					{"isExactMatch": true, "fieldName": "Web_Order_Id__c", "doCreate": true, "doFind": false, "label": "Web Order Id" },
					{"isExactMatch": true, "fieldName": "Live_Chat_Question_Summary__c", "doCreate": true, "doFind": false, "label": "Live Chat Question Summary" },
					{"isExactMatch": true, "fieldName": "SuppliedName", "doCreate": true, "doFind": false, "label": "Web Name" },
					{"isExactMatch": true, "fieldName": "SuppliedEmail", "doCreate": true, "doFind": false, "label": "Web Email" },
					{"isExactMatch": true, "fieldName": "RoutedToButtonId__c", "doCreate": true, "doFind": false, "label": "RoutedToButtonId" }
				]
			},
			{
				"entityName": "Order__c",
				"linkToEntityName": "Case",
				"linkToEntityField": "Related_Order__c",
				"saveToTranscript": "Order__c",
				"showOnCreate": true,
				"entityFieldMaps": [
					{"isExactMatch": true, "fieldName": "Name", "doCreate": false, "doFind": true, "label": "Web Order Id", "displayToAgent": true }
				]
			}
		];

        embedded_svc.init(
            BH_MYSALESFORCE_DOMAIN,
            BH_SALESFORCE_DOMAIN,
            gslbBaseURL,
            SALESFORCE_ORG_ID,
            SNAPINS_DEPLOYMENT_NAME,
            {
                baseLiveAgentContentURL: SALESFORCE_LIVEAGENT_CONTENT_URL,
                deploymentId: SNAPINS_DEPLOYMENT_ID,
                buttonId: SNAPINS_BUTTON_ID,
                baseLiveAgentURL: SALESFORCE_LIVEAGENT_CHAT_URL,
                eswLiveAgentDevName: SNAPINS_DEPLOYMENT_NAME,
                isOfflineSupportEnabled: true
            }
        );

        embedded_svc.addEventHandler("onHelpButtonClick", onHelpButtonClick);

        if(options.onChatClose){
            embedded_svc.addEventHandler("afterDestroy", options.onChatClose);
        }

        embedded_svc.addEventHandler("onChatEstablished", function(data) {
            // setting the cookie valid for 2 minutes to restore the chat session in case when user refreshes the page
            if (window.bnh) {
                bnh.util.setCookie('liveChatConferenceInitiated', 'y', 120);    
            }
        });

        // disabling liveChatConferenceInitiated cookie when Embedded Service Chat has ended and the application is closed.
        embedded_svc.addEventHandler("afterDestroy", function(data) {
            if (window.bnh) {
                bnh.util.setCookie('liveChatConferenceInitiated', 'n');
            }
        });

    };

    function onHelpButtonClick(){
        if(options.onChatOpen){
            options.onChatOpen();
        }
        isChatSupportedCheck();
    }

    function isChatSupportedCheck() {
        var iframe = document.createElement("iframe");
        iframe.style.display = "none";
        iframe.src = BH_SALESFORCE_DOMAIN + "/SnapIns3PCstart";
        document.body.appendChild(iframe);
    }

    function loadScript(url, successCB, failCB) {
        var s = document.createElement('script');
        s.setAttribute('src', url);
        s.onload = successCB;
        s.onerror = failCB;
        document.body.appendChild(s);
    }
    function loadStylesheet(url) {
        var linkTag = document.createElement("link");
        linkTag.type = "text/css";
        linkTag.rel = "stylesheet";
        linkTag.href = url;
        document.getElementsByTagName("head")[0].appendChild(linkTag);
    }


    function _loadChat() {
        loadStylesheet(BH_SALESFORCE_DOMAIN + "/resource/SnapInsCssExt");
        loadScript(SALESFORCE_DOMAIN + '/embeddedservice/5.0/esw.min.js', function () {
                initESW(SALESFORCE_DOMAIN);
            },function () {
                loadScript(BH_MYSALESFORCE_DOMAIN + '/embeddedservice/5.0/esw.min.js', function () {
                    initESW(null);
                });
            });
    }
    
    function _openChat() {
        var snapInButton = document.querySelector(".embeddedServiceSidebarMinimizedDefaultUI"),
            chatIsMinimized = snapInButton && snapInButton.clientHeight !== 0;
    
        setDefaultChatQueue(chatQueue);

        if (chatIsMinimized) {
            snapInButton.click();

        } else /*if (chat is closed) */{
            embedded_svc.onHelpButtonClick();
        }
    }

    function openChat(options) {
        options = options || {};
        chatQueue = options.chatQueue;

        if (chatReady) {
            _openChat();
        } else {
            openChatOnLoad = true;
        }
    }

    return {
        openChat: openChat,
    }
    
    function setDefaultChatQueue(chatQueue) {
        embedded_svc.settings.prepopulatedPrechatFields = {};
        if (QUEUE_IDS.PRIMARY[chatQueue]) {
            embedded_svc.settings.prepopulatedPrechatFields.First_Option__c = QUEUE_IDS.PRIMARY[chatQueue]
        }
        if (QUEUE_IDS.SECONDARY[chatQueue]) {
            embedded_svc.settings.prepopulatedPrechatFields.Second_Option__c = QUEUE_IDS.SECONDARY[chatQueue]
        }
        
    }

}
