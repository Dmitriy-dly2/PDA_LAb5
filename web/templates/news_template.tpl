<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Новости</title>

    <link rel="stylesheet"
          href="//cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.2.12/semantic.min.css">
</head>

<body>
<div class="ui container" style="padding-top: 20px;">

    % if is_recommendations:
        <h2 class="ui header">Рекомендации</h2>
    % else:
        <h2 class="ui header">Неразмеченные новости</h2>
    % end

    <a href="/news" class="ui button">Все новости</a>
    <a href="/recommendations" class="ui primary button">Показать рекомендации</a>

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

        <tbody>
        % for row in rows:
            <tr>
                <td>
                    <a href="{{ row.url }}" target="_blank">
                        {{ row.title }}
                    </a>
                </td>

                <td>{{ row.author }}</td>

                % if is_recommendations:
                    <td>
                        % if row.predicted_label == 'good':
                            <span class="ui green label">Интересно</span>
                        % elif row.predicted_label == 'maybe':
                            <span class="ui yellow label">Возможно</span>
                        % elif row.predicted_label == 'never':
                            <span class="ui red label">Не интересно</span>
                        % else:
                            -
                        % end
                    </td>
                % else:
                    <td>
                        <a class="ui green button"
                           href="/add_label?label=good&id={{ row.id }}">
                            Интересно
                        </a>

                        <a class="ui yellow button"
                           href="/add_label?label=maybe&id={{ row.id }}">
                            Возможно
                        </a>

                        <a class="ui red button"
                           href="/add_label?label=never&id={{ row.id }}">
                            Не интересно
                        </a>
                    </td>
                % end
            </tr>
        % end
        </tbody>
    </table>

</div>
</body>
</html>