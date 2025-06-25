alert('JS do pedido carregado!');

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
    // Inicializar Select2 para cliente
    $('#id_cliente').select2({
        theme: 'bootstrap-5',
        width: '100%',
        language: {
            inputTooShort: function() {
                return 'Digite pelo menos 2 caracteres...';
            },
            searching: function() {
                return 'Buscando...';
            },
            noResults: function() {
                return 'Nenhum resultado encontrado';
            }
        }
    });

    // Função para inicializar Select2 e preencher preço
    function inicializarSelect2Produto(container) {
        container.find('.produto-select').select2({
            theme: 'bootstrap-5',
            placeholder: 'Busque por nome, código ou EAN do produto',
            minimumInputLength: 2,
            ajax: {
                url: '/produtos/api/buscar/',
                dataType: 'json',
                delay: 250,
                data: function (params) {
                    return { term: params.term };
                },
                processResults: function (data) {
                    return {
                        results: data.results
                    };
                }
            },
            templateResult: function(produto) {
                if (!produto.id) return produto.text;
                let preco = produto.preco ? `<span style='color:#388e3c;font-weight:bold;margin-left:8px;'>R$ ${produto.preco}</span>` : '';
                let estoque = produto.estoque ? `<span style='color:#888;margin-left:8px;'>Estoque: ${produto.estoque}</span>` : '';
                return $(`<span><i class='fas fa-box' style='margin-right:6px;color:#1976d2;'></i>${produto.text} ${preco} ${estoque}</span>`);
            },
            templateSelection: function(produto) {
                return produto.text || produto.id;
            },
            width: 'resolve'
        }).on('select2:select', function(e) {
            var data = e.params.data;
            var itemForm = $(this).closest('.item-form');
            if (data.preco && itemForm.length) {
                itemForm.find('input[name$="preco_unitario"]').val(data.preco);
            }
        });
    }

    // Inicializa Select2 para os itens já existentes
    $('#formset-container .item-form').each(function() {
        inicializarSelect2Produto($(this));
    });

    // Função para calcular subtotal
    function calcularSubtotal(itemForm) {
        var quantidade = parseFloat(itemForm.find('input[name$="quantidade"]').val()) || 0;
        var preco = parseFloat(itemForm.find('input[name$="preco_unitario"]').val()) || 0;
        var desconto = parseFloat(itemForm.find('input[name$="desconto_item"]').val()) || 0;
        var subtotal = quantidade * preco;
        if (desconto > 0) {
            subtotal = subtotal - (subtotal * (desconto / 100));
        }
        itemForm.find('.subtotal-display').val(subtotal.toFixed(2));
        calcularTotal();
    }

    // Eventos para calcular subtotal
    $(document).on('change', 'input[name$="quantidade"], input[name$="preco_unitario"], input[name$="desconto_item"]', function() {
        var itemForm = $(this).closest('.item-form');
        calcularSubtotal(itemForm);
    });

    // Calcular total quando mudar desconto ou taxa
    $('#id_desconto, #id_taxa_entrega').on('change', calcularTotal);

    // Adicionar novo item
    $('#add-item').on('click', function(e) {
        e.preventDefault();
        var emptyForm = $('#empty-form .item-form').clone(true);
        var totalForms = $('#id_' + $('#formset-container').attr('id').replace('-', '_') + '-TOTAL_FORMS');
        var formCount = parseInt(totalForms.val());
        emptyForm.find(':input').each(function() {
            var name = $(this).attr('name').replace('__prefix__', formCount);
            var id = $(this).attr('id').replace('__prefix__', formCount);
            $(this).attr({'name': name, 'id': id});
        });
        $('#formset-container').append(emptyForm);
        totalForms.val(formCount + 1);
        inicializarSelect2Produto(emptyForm);
    });

    // Remover item
    $(document).on('click', '.remove-item', function(e) {
        e.preventDefault();
        var itemForm = $(this).closest('.item-form');
        itemForm.remove();
        calcularTotal();
    });
}); 