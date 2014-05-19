<table class="data-table display" cellspacing="0" width="100%">
    <thead>
        <tr>
            % for column in table.columns:
                <th>{{column}}</th>
            % end
        </tr>
    </thead>
    <tbody>
    % for row in table.to_records(index=False):
        <tr>
        % for elem in row:
            <td>{{elem}}</td>
        % end
        </tr>
    % end 
    </tbody>
</table>
