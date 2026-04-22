# Sistema de Toast e Dialog de Confirmação - Vittas

## 📋 Visão Geral

Sistema global de notificações (toasts) e confirmação de exclusão reutilizável em todo o projeto Vittas.

## 🎯 Componentes

### 1. Toast Manager (`toast-manager.js`)
Gerenciador de notificações tipo toast com suporte a múltiplos tipos.

### 2. Toast Template (`templates/includes/toast.html`)
Template visual do toast no topo central da tela.

### 3. Confirm Dialog (`templates/includes/confirm_dialog.html`)
Dialog modal para confirmação de ações destrutivas (exclusão).

## 🚀 Como Usar

### Exibindo Toasts

#### Método 1: Via Evento Customizado (Recomendado)
```javascript
// Toast de sucesso
window.dispatchEvent(new CustomEvent('show-toast', {
  detail: {
    type: 'success',
    message: 'Operação realizada com sucesso!'
  }
}));

// Toast de erro  
window.dispatchEvent(new CustomEvent('show-toast', {
  detail: {
    type: 'error',
    message: 'Erro ao processar a requisição.'
  }
}));

// Toast de aviso
window.dispatchEvent(new CustomEvent('show-toast', {
  detail: {
    type: 'warning',
    message: 'Atenção: verifique os dados inseridos.'
  }
}));

// Toast informativo
window.dispatchEvent(new CustomEvent('show-toast', {
  detail: {
    type: 'info',
    message: 'Processamento em andamento...'
  }
}));
```

#### Método 2: Acesso Direto ao Componente
```javascript
// Obter instância do toast
const toast = document.querySelector('[x-data="toastManager()"]').__x.$data;

// Métodos disponíveis
toast.success('Mensagem de sucesso');
toast.error('Mensagem de erro');
toast.warning('Mensagem de aviso');
toast.info('Mensagem informativa');
toast.show('success', 'Mensagem customizada');
toast.hide(); // Fecha manualmente
```

### Usando o Dialog de Confirmação

```javascript
// Forma recomendada: usar helper function global
window.openConfirmDialog(
  '/url/para/exclusao/',  // URL da ação
  () => {
    // Callback após exclusão bem-sucedida
    window.dispatchEvent(new CustomEvent('show-toast', {
      detail: {
        type: 'success',
        message: 'Registro excluído com sucesso!'
      }
    }));
    setTimeout(() => window.location.reload(), 1500);
  },
  () => {
    // Callback opcional ao cancelar (opcional)
    console.log('Exclusão cancelada');
  }
);

// Alternativa: acessar diretamente via Alpine (não recomendado)
const confirmDialog = document.querySelector('#confirm_delete_modal').__x.$data;
confirmDialog.open('/url/para/exclusao/', onConfirm, onCancel);
```
    // Callback executado após exclusão bem-sucedida
    window.dispatchEvent(new CustomEvent('show-toast', {
      detail: {
        type: 'success',
        message: 'Registro excluído com sucesso!'
      }
    }));
    
    setTimeout(() => {
      window.location.reload();
    }, 1500);
  },
  () => {
    // Callback opcional executado ao cancelar
    console.log('Exclusão cancelada');
  }
);
```

## 🎨 Comportamento dos Toasts

### Fechamento Automático
- **Success** (verde): Fecha automaticamente em 4 segundos
- **Info** (azul): Fecha automaticamente em 4 segundos
- **Warning** (amarelo): Permanece até ser fechado manualmente
- **Error** (vermelho): Permanece até ser fechado manualmente

### Botão de Fechar
Toasts de erro e aviso exibem um botão (X) para fechamento manual.

## 📝 Exemplo Completo

### Em uma ListView com CRUD

```html
{% extends "base.html" %}

{% block content %}
<div x-data="meuCrud()" @keydown.escape.window="closeModal()">
  <div class="container mx-auto p-4">
    {% csrf_token %}
    
    <!-- Seus botões de ação -->
    <button @click="deleteItem('{% url 'app:delete' item.pk %}')">
      Excluir
    </button>
  </div>
</div>

<script>
  function meuCrud() {
    return {
      deleteItem(url) {
        window.openConfirmDialog(url, () => {
          window.dispatchEvent(new CustomEvent('show-toast', {
            detail: {
              type: 'success',
              message: 'Item excluído com sucesso!'
            }
          }));

          setTimeout(() => window.location.reload(), 1500);
        });
      }
    };
  }
</script>
{% endblock %}
```

## 🔧 Integração no Projeto

### Arquivos Modificados

1. **`templates/base.html`** - Inclui o script e os templates globais
2. **`static/js/toast-manager.js`** - Lógica dos componentes
3. **`templates/includes/toast.html`** - Template do toast
4. **`templates/includes/confirm_dialog.html`** - Template do dialog

### Disponibilidade

Os componentes estão disponíveis **automaticamente em todas as páginas** que estendem `base.html`.

## ✅ Vantagens

- **Reutilizável**: Não precisa duplicar código em cada tela
- **Consistente**: Mesma experiência em todo o sistema
- **Centralizado**: Fácil manutenção e atualização
- **Desacoplado**: Comunicação via eventos customizados  
- **Acessível**: Funciona em qualquer template Django

## 🎯 Boas Práticas

1. **Use eventos customizados** para toasts em funções reutilizáveis
2. **Sempre forneça feedback** ao usuário após ações importantes
3. **Use o tipo correto** de toast para cada situação
4. **Personalize as mensagens** para serem claras e específicas
5. **Combine toast com dialog** para ações destrutivas

## 📚 Referências

- Alpine.js: https://alpinejs.dev/
- DaisyUI Alerts: https://daisyui.com/components/alert/
- DaisyUI Modals: https://daisyui.com/components/modal/

---

**Projeto**: Vittas  
**Data**: Fevereiro 2026  
**Versão**: 1.0
