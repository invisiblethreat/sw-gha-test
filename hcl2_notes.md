# HCL2 (Terraform)

## This is a variable assignment to a string

```terraform
type = "AWS"
```

Tree:

```text
attribute
  identifier    type
  expr_term
    string_lit  AWS
  new_line_or_comment
```

## This is an array

```terraform
actions = [
    "s3:PutObjectAcl",
]
```

Tree

```text
attribute
  identifier        actions
  expr_term
    tuple
      new_line_or_comment

      expr_term
        string_lit  s3:PutObjectAcl
      new_line_or_comment

  new_line_or_comment
```

## Object element

```terraform
variable "azs" {
  default = {
    us-west-1      = "us-west-1c,us-west-1b"
  }
}
```

Tree:

```text
object_elem
  identifier      us-west-1
  expr_term
    string_lit    us-west-1c,us-west-1b
```

## Conditionals

```terraform
count                  = var.tgw_name == "" ? 0 : var.number_of_az
```

Tree:

```text
attribute
  identifier    count
  binary_op
    expr_term
      get_attr_expr_term
        expr_term
          identifier    var
        identifier      tgw_name
    binary_term
      binary_operator   ==
      conditional
        expr_term
          string_lit
        expr_term
          int_lit       0
        expr_term
          get_attr_expr_term
            expr_term
              identifier        var
            identifier  number_of_az
  new_line_or_comment
```

## Variable block containing an object

```terraform
variable "azs" {
  default = {
    us-west-1      = "us-west-1c,us-west-1b"
    us-west-2      = "us-west-2c,us-west-2b,us-west-2a"
    us-east-1      = "us-east-1c,us-east-1b,us-east-1a"
    eu-central-1   = "eu-central-1a,eu-central-1b,eu-central-1c"
    sa-east-1      = "sa-east-1a,sa-east-1c"
    ap-northeast-1 = "ap-northeast-1a,ap-northeast-1c,ap-northeast-1d"
    ap-southeast-1 = "ap-southeast-1a,ap-southeast-1b,ap-southeast-1c"
    ap-southeast-2 = "ap-southeast-2a,ap-southeast-2b,ap-southeast-2c"
  }
}
```

Tree:

```text
block
  identifier        variable
  string_lit        azs
  new_line_or_comment

  body
    attribute
      identifier    default
      expr_term
        object
          new_line_or_comment

          object_elem
            identifier      us-west-1
            expr_term
              string_lit    us-west-1c,us-west-1b
          new_line_and_or_comma
            new_line_or_comment

          object_elem
            identifier      us-west-2
            expr_term
              string_lit    us-west-2c,us-west-2b,us-west-2a
          new_line_and_or_comma
            new_line_or_comment

          object_elem
            identifier      us-east-1
            expr_term
              string_lit    us-east-1c,us-east-1b,us-east-1a
          new_line_and_or_comma
            new_line_or_comment

          object_elem
            identifier      eu-central-1
            expr_term
              string_lit    eu-central-1a,eu-central-1b,eu-central-1c
          new_line_and_or_comma
            new_line_or_comment

          object_elem
            identifier      sa-east-1
            expr_term
              string_lit    sa-east-1a,sa-east-1c
          new_line_and_or_comma
            new_line_or_comment

          object_elem
            identifier      ap-northeast-1
            expr_term
              string_lit    ap-northeast-1a,ap-northeast-1c,ap-northeast-1d
          new_line_and_or_comma
            new_line_or_comment

          object_elem
            identifier      ap-southeast-1
            expr_term
              string_lit    ap-southeast-1a,ap-southeast-1b,ap-southeast-1c
          new_line_and_or_comma
            new_line_or_comment

          object_elem
            identifier      ap-southeast-2
            expr_term
              string_lit    ap-southeast-2a,ap-southeast-2b,ap-southeast-2c
          new_line_and_or_comma
            new_line_or_comment

      new_line_or_comment

  new_line_or_comment
```

## Attributes like this cause a parsing issue because they are missing a newline at the end of the file

```terraform
foo = "bar"
arr = ["foo", "bar"]
```

But with a new line added:
Tree:

```text
start
  body
    attribute
      identifier        foo
      expr_term
        string_lit      bar
      new_line_or_comment

    attribute
      identifier        arr
      expr_term
        tuple
          expr_term
            string_lit  foo
          expr_term
            string_lit  bar
      new_line_or_comment
```
