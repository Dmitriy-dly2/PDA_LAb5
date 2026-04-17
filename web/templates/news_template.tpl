<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ML News</title>

    <link rel="stylesheet"
          href="//cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.2.12/semantic.min.css">

    <style>
        .main-container {
            padding-top: 30px;
            padding-bottom: 50px;
        }

        .stats-box {
            margin-bottom: 20px !important;
        }

        .label-buttons {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .label-buttons button {
            flex: 1;
        }

        .row-updated {
            background: #f6ffed !important;
            transition: 0.3s;
        }

        .accuracy-box {
            margin-top: 10px;
            margin-bottom: 20px;
        }
    </style>
</head>

<body>
<div class="ui container main-container">


    <!-- ========================= -->
    <!-- HEADER -->
    <!-- ========================= -->

    % if is_recommendations:

        <h2 class="ui header">Рекомендованные новости</h2>

        % if defined('accuracy'):
            <div class="ui message info accuracy-box">
                <b>Точность модели:</b> {{accuracy}}%
            </div>
        % end

    % else:

        <h2 class="ui header">Разметка новостей для обучения ML</h2>

        <div class="ui message info stats-box">
            <i class="info circle icon"></i>
            Вам осталось разметить:
            <strong id="counter">{{len(rows)}}</strong> новостей.
        </div>

    % end


    <!-- ========================= -->
    <!-- NAV -->
    <!-- ========================= -->

    <div style="margin-bottom: 20px;">
        <a href="/news" class="ui button">Обучение</a>
        <a href="/recommendations" class="ui primary button">Рекомендации</a>
    </div>


    <!-- ========================= -->
    <!-- TABLE -->
    <!-- ========================= -->

    <table class="ui celled table">
        <thead>
        <tr>
            <th>Title</th>
            <th>Author</th>

            % if is_recommendations:
                <th>Prediction</th>
            % else:
                <th>Label</th>
            % end
        </tr>
        </thead>

        <tbody id="table-body">

        % for row in rows:
        <tr id="row-{{row.id}}" data-habr-id="{{row.habr_id}}">

            <td>
                <a href="{{row.url}}" target="_blank">
                    {{row.title}}
                </a>
            </td>

            <td>{{row.author}}</td>

            % if is_recommendations:

                <td>
                    % if getattr(row, "predicted_label", None) == 'good':
                        <span class="ui green label">Интересно</span>
                    % elif getattr(row, "predicted_label", None) == 'maybe':
                        <span class="ui yellow label">Возможно</span>
                    % elif getattr(row, "predicted_label", None) == 'never':
                        <span class="ui red label">Не интересно</span>
                    % else:
                        -
                    % end
                </td>

            % else:

                <td>
                    <div class="label-buttons">

                        <button class="ui green button"
                                onclick="sendLabel('{{row.habr_id}}', 'good')">
                            Интересно
                        </button>

                        <button class="ui yellow button"
                                onclick="sendLabel('{{row.habr_id}}', 'maybe')">
                            Возможно
                        </button>

                        <button class="ui red button"
                                onclick="sendLabel('{{row.habr_id}}', 'never')">
                            Не интересно
                        </button>

                    </div>
                </td>

            % end

        </tr>
        % end

        </tbody>
    </table>

</div>


<!-- ========================= -->
<!-- LIVE UPDATE -->
<!-- ========================= -->

<script>

async function sendLabel(habr_id, label) {

    const res = await fetch(`/add_label?id=${habr_id}&label=${label}`);

    if (res.ok) {
        // Находим строку по data-habr-id
        const rows = document.querySelectorAll("#table-body tr");

        for (let row of rows) {
            if (row.getAttribute('data-habr-id') === habr_id) {
                row.classList.add("row-updated");

                setTimeout(() => {
                    row.remove();
                    updateCounter();
                }, 300);
                break;
            }
        }
    }
}

function updateCounter() {
    const counter = document.getElementById("counter");

    if (!counter) return;

    const rows = document.querySelectorAll("#table-body tr");
    counter.innerText = rows.length;
}

</script>

</body>
</html>