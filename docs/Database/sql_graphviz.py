#!/usr/bin/env python
# https://github.com/rm-hull/sql_graphviz
# run  dot -Tpdf schema.dot > schema.pdf
import sys
from datetime import datetime
from pyparsing import alphas, alphanums, Literal, Word, Forward, OneOrMore, ZeroOrMore, CharsNotIn, Suppress, QuotedString, Optional


def field_act(s, loc, tok):
    return '<tr><td bgcolor="grey96" align="left" port="{0}"><font face="Times-bold">{0}</font>  <font color="#535353">{1}</font></td></tr>'.format(tok[0].replace('"', ''), ' '.join(tok[1::]).replace('"', '\\"'))


def field_list_act(s, loc, tok):
    return "\n        ".join(tok)


def create_table_act(s, loc, tok):
    return '''
  "{tableName}" [
    shape=none
    label=<
      <table border="0" cellspacing="0" cellborder="1">
        <tr><td bgcolor="lightblue2"><font face="Times-bold" point-size="20">{tableName}</font></td></tr>
        {fields}
      </table>
    >];'''.format(**tok)


def add_fkey_act(s, loc, tok):
    return '  "{tableName}":{keyName} -> "{fkTable}":{fkCol}'.format(**tok)


def other_statement_act(s, loc, tok):
    return ""


def grammar():
    parenthesis = Forward()
    parenthesis <<= "(" + ZeroOrMore(CharsNotIn("()") | parenthesis) + ")"

    field_def = OneOrMore(Word(alphanums + "_\"'`:-") | parenthesis)
    field_def.setParseAction(field_act)

    tablename_def = ( Word(alphas + "`_") | QuotedString("\"") )

    field_list_def = field_def + ZeroOrMore(Suppress(",") + field_def)
    field_list_def.setParseAction(field_list_act)

    create_table_def = Literal("CREATE") + "TABLE" + tablename_def.setResultsName("tableName") + "(" + field_list_def.setResultsName("fields") + ")" + ";"
    create_table_def.setParseAction(create_table_act)

    add_fkey_def = Literal("FOREIGN") + "KEY" + "(" + Word(alphanums).setResultsName("keyName") + ")" + "REFERENCES" + Word(alphanums).setResultsName("fkTable") + "(" + Word(alphanums + "_").setResultsName("fkCol") + ")" + Optional(Literal("DEFERRABLE")) + ";"
    add_fkey_def.setParseAction(add_fkey_act)

    other_statement_def = OneOrMore(CharsNotIn(";")) + ";"
    other_statement_def.setParseAction(other_statement_act)

    comment_def = "--" + ZeroOrMore(CharsNotIn("\n"))
    comment_def.setParseAction(other_statement_act)

    return OneOrMore(comment_def | create_table_def | add_fkey_def | other_statement_def)


def graphviz(filename):
    print("/*")
    print(" * Graphviz of '%s', created %s" % (filename, datetime.now()))
    print(" * Generated from https://github.com/rm-hull/sql_graphviz")
    print(" */")
    print("digraph g { graph [ rankdir = \"LR\" ];")

    for i in grammar().parseFile(filename):
        if i != "":
            print(i)
    print("}")

if __name__ == '__main__':
    filename = sys.stdin if len(sys.argv) == 1 else sys.argv[1]
    graphviz(filename)
