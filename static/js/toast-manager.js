/**
 * Toast Manager Global
 * Sistema de notificações reutilizável para todo o projeto Vittas
 */
window.toastManager = function () {
  return {
    showToast: false,
    toastType: 'success',
    toastMessage: '',
    toastTimeout: null,

    /**
     * Exibe um toast com tipo e mensagem
     * @param {string} type - success, error, warning, info
     * @param {string} message - Mensagem a ser exibida
     */
    show(type, message) {
      // Limpa timeout anterior se existir
      if (this.toastTimeout) {
        clearTimeout(this.toastTimeout);
        this.toastTimeout = null;
      }

      this.toastType = type;
      this.toastMessage = message;
      this.showToast = true;

      // Auto-fecha apenas toasts de sucesso (4 segundos)
      // Toasts de erro permanecem até serem fechados manualmente
      if (type === 'success' || type === 'info') {
        this.toastTimeout = setTimeout(() => {
          this.hide();
        }, 4000);
      }
    },

    /**
     * Esconde o toast manualmente
     */
    hide() {
      this.showToast = false;
      if (this.toastTimeout) {
        clearTimeout(this.toastTimeout);
        this.toastTimeout = null;
      }
    },

    // Atalhos para tipos específicos
    success(message) {
      this.show('success', message);
    },

    error(message) {
      this.show('error', message);
    },

    warning(message) {
      this.show('warning', message);
    },

    info(message) {
      this.show('info', message);
    }
  };
};

/**
 * Confirm Dialog Manager Global
 * Sistema de confirmação de exclusão reutilizável para todo o projeto
 */
window.confirmDialogManager = function () {
  return {
    isDeleting: false,
    deleteUrl: '',
    csrfToken: '',
    onConfirmCallback: null,
    onCancelCallback: null,
    dialogTitle: 'Confirmar Exclusao',
    dialogMessage: 'Tem certeza que deseja excluir este registro?',
    dialogDetail: 'Esta acao nao pode ser desfeita.',
    confirmLabel: 'Excluir',
    confirmIcon: 'fas fa-trash',
    confirmButtonClass: 'btn-error',
    requestMethod: 'POST',
    requestHeaders: {},

    init() {
      this.csrfToken = this.getCsrfToken();
      
      // Escuta eventos customizados para abrir o diálogo
      window.addEventListener('open-confirm-dialog', (event) => {
        this.open(event.detail || {});
      });
    },

    getCsrfToken() {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; csrftoken=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
      
      const input = document.querySelector('[name=csrfmiddlewaretoken]');
      return input ? input.value : '';
    },

    /**
     * Abre o dialog de confirmação
     * @param {string} url - URL para a ação de exclusão
     * @param {function} onConfirm - Callback executado após confirmação bem-sucedida
     * @param {function} onCancel - Callback executado ao cancelar (opcional)
     */
    open(options = {}) {
      this.deleteUrl = options.url || '';
      this.onConfirmCallback = options.onConfirm || null;
      this.onCancelCallback = options.onCancel || null;
      this.dialogTitle = options.title || 'Confirmar Exclusao';
      this.dialogMessage = options.message || 'Tem certeza que deseja excluir este registro?';
      this.dialogDetail = options.detail || 'Esta acao nao pode ser desfeita.';
      this.confirmLabel = options.confirmLabel || 'Excluir';
      this.confirmIcon = options.confirmIcon || 'fas fa-trash';
      this.confirmButtonClass = options.confirmButtonClass || 'btn-error';
      this.requestMethod = options.method || 'POST';
      this.requestHeaders = options.headers || {};
      
      if (this.$refs.confirmModal) {
        this.$refs.confirmModal.showModal();
      }
    },

    /**
     * Cancela e fecha o dialog
     */
    cancel() {
      if (this.$refs.confirmModal) {
        this.$refs.confirmModal.close();
      }
      
      this.deleteUrl = '';
      this.isDeleting = false;
      this.resetState();
      
      if (this.onCancelCallback) {
        this.onCancelCallback();
      }
    },

    resetState() {
      this.dialogTitle = 'Confirmar Exclusao';
      this.dialogMessage = 'Tem certeza que deseja excluir este registro?';
      this.dialogDetail = 'Esta acao nao pode ser desfeita.';
      this.confirmLabel = 'Excluir';
      this.confirmIcon = 'fas fa-trash';
      this.confirmButtonClass = 'btn-error';
      this.requestMethod = 'POST';
      this.requestHeaders = {};
      this.onConfirmCallback = null;
      this.onCancelCallback = null;
    },

    /**
     * Confirma e executa a exclusão
     */
    async confirm() {
      if (this.isDeleting) return;

      this.isDeleting = true;

      try {
        if (!this.deleteUrl) {
          if (this.$refs.confirmModal) {
            this.$refs.confirmModal.close();
          }

          if (this.onConfirmCallback) {
            await this.onConfirmCallback();
          }
          return;
        }

        const response = await fetch(this.deleteUrl, {
          method: this.requestMethod,
          headers: {
            'X-CSRFToken': this.csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
            ...this.requestHeaders,
          }
        });

        if (!response.ok) {
          throw new Error('Erro na requisição');
        }

        const data = await response.json();
        
        if (data.success) {
          if (this.$refs.confirmModal) {
            this.$refs.confirmModal.close();
          }
          
          if (this.onConfirmCallback) {
            this.onConfirmCallback();
          } else {
            // Comportamento padrão: recarrega a página
            window.location.reload();
          }
        } else {
          throw new Error(data.message || 'Erro ao excluir registro');
        }
      } catch (error) {
        console.error('Erro na exclusão:', error);
        
        // Emite evento para o toast mostrar o erro
        window.dispatchEvent(new CustomEvent('show-toast', {
          detail: {
            type: 'error',
            message: error.message || 'Erro ao excluir. Tente novamente.'
          }
        }));

        if (this.$refs.confirmModal) {
          this.$refs.confirmModal.close();
        }
      } finally {
        this.isDeleting = false;
        this.deleteUrl = '';
        this.resetState();
      }
    }
  };
};

/**
 * Helper function para abrir o diálogo de confirmação
 * Usa eventos customizados para facilitar o acesso ao componente
 * 
 * @param {string} url - URL para a ação de exclusão
 * @param {function} onConfirm - Callback executado após confirmação bem-sucedida
 * @param {function} onCancel - Callback executado ao cancelar (opcional)
 */
window.openConfirmDialog = function(urlOrOptions, onConfirm = null, onCancel = null) {
  const detail = typeof urlOrOptions === 'string'
    ? {
        url: urlOrOptions,
        onConfirm: onConfirm,
        onCancel: onCancel
      }
    : (urlOrOptions || {});

  // Despacha evento customizado que será capturado pelo diálogo
  window.dispatchEvent(new CustomEvent('open-confirm-dialog', {
    detail
  }));
};
