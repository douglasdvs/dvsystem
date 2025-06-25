document.addEventListener('DOMContentLoaded', function() {
  const formsetPrefix = 'itempedido_set';  // Ajuste para o prefixo do seu formset

  // Botão para adicionar um novo item
  const addBtn = document.getElementById('add-item');
  const totalFormsInput = document.querySelector(`input[name="${formsetPrefix}-TOTAL_FORMS"]`);
  const formsetTableBody = document.querySelector('#formset-table tbody');

  addBtn.addEventListener('click', function() {
    const totalForms = parseInt(totalFormsInput.value);
    const emptyRow = document.querySelector(`#empty-form`).innerHTML;
    const newRowHtml = emptyRow.replace(/__prefix__/g, totalForms);
    formsetTableBody.insertAdjacentHTML('beforeend', newRowHtml);
    totalFormsInput.value = totalForms + 1;

    // Adiciona event listeners para os campos do novo formulário
    addListenersToRow(formsetTableBody.lastElementChild);
  });

  // Função para adicionar os eventos necessários em uma linha do formset
  function addListenersToRow(row) {
    const produtoSelect = row.querySelector(`select[name$="-produto"]`);
    const quantidadeInput = row.querySelector(`input[name$="-quantidade"]`);
    const precoInput = row.querySelector(`input[name$="-preco_unitario"]`);
    const subtotalInput = row.querySelector(`input[name$="-subtotal"]`);
    const deleteCheckbox = row.querySelector(`input[name$="-DELETE"]`);

    // Atualiza preço ao mudar produto
    produtoSelect.addEventListener('change', function() {
      const produtoId = this.value;
      if (!produtoId) {
        precoInput.value = '';
        subtotalInput.value = '';
        return;
      }

      fetch(`/api/produtos/${produtoId}/preco/`)  // Sua API para retornar o preço JSON
        .then(response => response.json())
        .then(data => {
          precoInput.value = data.preco_venda;
          calculaSubtotal();
        })
        .catch(() => {
          precoInput.value = '';
          subtotalInput.value = '';
        });
    });

    // Recalcula subtotal ao mudar quantidade
    quantidadeInput.addEventListener('input', calculaSubtotal);

    // Recalcula subtotal ao mudar preço (se quiser liberar edição)
    precoInput.addEventListener('input', calculaSubtotal);

    // Se marcar para deletar, esconde a linha
    if(deleteCheckbox) {
      deleteCheckbox.addEventListener('change', function() {
        if (this.checked) {
          row.style.display = 'none';
        } else {
          row.style.display = '';
        }
      });
    }

    function calculaSubtotal() {
      let quantidade = parseFloat(quantidadeInput.value) || 0;
      let preco = parseFloat(precoInput.value) || 0;
      subtotalInput.value = (quantidade * preco).toFixed(2);
    }
  }

  // Inicializa os event listeners das linhas já existentes
  document.querySelectorAll('#formset-table tbody tr').forEach(addListenersToRow);
});
