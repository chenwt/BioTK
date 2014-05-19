% rebase('common/base.tpl', subtitle="Genomic region coexpression")

<h4>Query a genomic region to determine coexpressed genes.</h4>

<form method="POST">
<table>

<tr>
    <td>Genome:</td>
    <td>
        <select name="genome">
            <option value="hg19">hg19</option>
        </select>
    </td>
</tr>

<tr>
    <td>Region:</td>
    <td>
        <input name="region" type="text" value="chr1:1-1000" />
    </td>
</tr>

</table>

<input type="submit" />
</form>
