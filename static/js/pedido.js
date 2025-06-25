// Função para calcular total
function calcularTotal() {
    var total = 0;
    $('.subtotal-display').each(function() {
        total += parseFloat($(this).val()) || 0;
    });
    
    var desconto = parseFloat($('#id_desconto').val()) || 0;
    var taxa = parseFloat($('#id_taxa_entrega').val()) || 0;
    
    if (desconto > 0) {
        total = total - (total * (desconto / 100));
    }
    
    total += taxa;
    
    $('#total_pedido').text(total.toFixed(2));
}

$(document).ready(function() {
    // Inicialização do Select2 para todos os selects
    $('.produto-select').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Digite o nome ou código do produto',
        allowClear: true,
        language: {
            noResults: function() {
                return "Nenhum produto encontrado";
            },
            searching: function() {
                return "Buscando...";
            }
        }
    });

    // Função para formatar valores monetários
    function formatMoney(value) {
        return parseFloat(value).toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    // Função para calcular o subtotal de um item
    function calcularSubtotal(itemForm) {
        const quantidade = parseFloat(itemForm.find('[name$="-quantidade"]').val()) || 0;
        const precoUnitario = parseFloat(itemForm.find('[name$="-preco_unitario"]').val()) || 0;
        const descontoItem = parseFloat(itemForm.find('[name$="-desconto_item"]').val()) || 0;
        
        let subtotal = quantidade * precoUnitario;
        if (descontoItem > 0) {
            subtotal = subtotal * (1 - (descontoItem / 100));
        }
        
        itemForm.find('.subtotal-display').val(formatMoney(subtotal));
        return subtotal;
    }

    // Função para calcular o total do pedido
    function calcularTotalPedido() {
        let total = 0;
        $('.item-form').each(function() {
            total += calcularSubtotal($(this));
        });

        const desconto = parseFloat($('#id_desconto').val()) || 0;
        const taxaEntrega = parseFloat($('#id_taxa_entrega').val()) || 0;

        if (desconto > 0) {
            total = total * (1 - (desconto / 100));
        }

        total += taxaEntrega;
        $('#total_pedido').text(formatMoney(total));
    }

    // Adicionar novo item
    $('#add-item').click(function() {
        const totalForms = $('#id_itens-TOTAL_FORMS');
        const formCount = parseInt(totalForms.val());
        const emptyForm = $('#empty-form').html().replace(/__prefix__/g, formCount);
        
        $('#formset-container').append(emptyForm);
        totalForms.val(formCount + 1);

        // Inicializar Select2 no novo item
        const newForm = $('.item-form').last();
        newForm.find('.produto-select').select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: 'Digite o nome ou código do produto',
            allowClear: true
        });

        // Adicionar animação
        newForm.hide().fadeIn(300);
    });

    // Remover item
    $(document).on('click', '.remove-item', function() {
        const itemForm = $(this).closest('.item-form');
        itemForm.fadeOut(300, function() {
            $(this).remove();
            calcularTotalPedido();
        });
    });

    // Atualizar preço unitário ao selecionar produto
    $(document).on('change', '.produto-select', function() {
        const itemForm = $(this).closest('.item-form');
        const produtoId = $(this).val();
        
        if (produtoId) {
            $.get('/pedidos/ajax/preco-produto/', { produto_id: produtoId }, function(data) {
                if (data.preco !== undefined) {
                    itemForm.find('[name$="-preco_unitario"]').val(data.preco);
                    calcularSubtotal(itemForm);
                    calcularTotalPedido();
                } else {
                    alert('Preço do produto não encontrado.');
                }
            }).fail(function(xhr) {
                alert('Erro ao buscar o preço do produto.');
            });
        }
    });

    // Recalcular ao mudar quantidade, preço ou desconto
    $(document).on('input', '[name$="-quantidade"], [name$="-preco_unitario"], [name$="-desconto_item"]', function() {
        const itemForm = $(this).closest('.item-form');
        calcularSubtotal(itemForm);
        calcularTotalPedido();
    });

    // Recalcular ao mudar desconto geral ou taxa de entrega
    $('#id_desconto, #id_taxa_entrega').on('input', function() {
        calcularTotalPedido();
    });

    // Validação do formulário
    $('#pedido-form').on('submit', function(e) {
        let isValid = true;
        
        // Validar campos obrigatórios
        $(this).find('[required]').each(function() {
            if (!$(this).val()) {
                $(this).addClass('is-invalid');
                isValid = false;
            } else {
                $(this).removeClass('is-invalid');
            }
        });

        // Validar se há pelo menos um item
        if ($('.item-form').length === 0) {
            alert('Adicione pelo menos um item ao pedido');
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
            alert('Por favor, preencha todos os campos obrigatórios');
        }
    });

    // Feedback visual para campos obrigatórios
    $('input, select').on('input change', function() {
        if ($(this).prop('required')) {
            if ($(this).val()) {
                $(this).removeClass('is-invalid').addClass('is-valid');
            } else {
                $(this).removeClass('is-valid').addClass('is-invalid');
            }
        }
    });

    // Inicializar cálculos
    calcularTotalPedido();
}); 