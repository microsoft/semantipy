# Operations

## Apply

### semantipy.apply(s: SemanticTypeA, changes: [Semantics](#semantipy.Semantics) | str, /) → SemanticTypeA

### semantipy.apply(s: SemanticTypeA, where: [Semantics](#semantipy.Semantics) | str, changes: [Semantics](#semantipy.Semantics) | str, /) → SemanticTypeA

### semantipy.apply(s: str, changes: [Semantics](#semantipy.Semantics) | str, /) → [Text](#semantipy.Text)

### semantipy.apply(s: str, where: [Semantics](#semantipy.Semantics) | str, changes: [Semantics](#semantipy.Semantics) | str, /) → [Text](#semantipy.Text)

Apply changes to a semantic object.

Apply comes with two signatures:

1. apply(s: SemanticType, changes: Semantics | str) -> SemanticType
2. apply(s: SemanticType, where: Semantics | str, changes: Semantics | str) -> SemanticType

## Cast

### semantipy.cast(s: [Semantics](#semantipy.Semantics) | str, return_type: type[SemanticTypeA]) → SemanticTypeA

Cast a semantic object to a different type.
The operation does not change the semantics of the object.

Based on the implementation, it may add or change some information to the original object.
For example, casting a Text object to a PythonFunction object may generate code solely based on little information.
It’s recommended to use evaluate in this case for clarity.
It’s up to the implementation to decide the extent to which the object can be changed.

## Combine

### semantipy.combine(\*semantics: [Semantics](#semantipy.Semantics) | str) → [Semantics](#semantipy.Semantics)

This function takes multiple semantic objects or strings and combines them into a single semantic object.
The input can be a mix of Semantics objects and strings.
The function  is designed to handle various types of semantic inputs and merge them into a cohesive whole.

## Contains

### semantipy.contains(s: [Semantics](#semantipy.Semantics), t: [Semantics](#semantipy.Semantics)) → bool

## Context

### semantipy.context(\*ctx: [Semantics](#semantipy.Semantics) | str)

## Diff

### semantipy.diff(s: [Semantics](#semantipy.Semantics) | str, t: [Semantics](#semantipy.Semantics) | str) → [Semantics](#semantipy.Semantics)

Compute the difference between two semantic objects.

## Equals

### semantipy.equals(s: [Semantics](#semantipy.Semantics), t: [Semantics](#semantipy.Semantics)) → bool

## Logical Binary

### semantipy.logical_binary(operator: [Semantics](#semantipy.Semantics), s: [Semantics](#semantipy.Semantics) | str, t: [Semantics](#semantipy.Semantics) | str) → bool

## Logical Unary

### semantipy.logical_unary(operator: [Semantics](#semantipy.Semantics), s: [Semantics](#semantipy.Semantics) | str) → bool

## Resolve

### semantipy.resolve(s: [Semantics](#semantipy.Semantics) | str, return_type: type[SemanticTypeA]) → SemanticTypeA

### semantipy.resolve(s: [Semantics](#semantipy.Semantics) | str) → [Semantics](#semantipy.Semantics)

Compute the value of a semantic expression.

Examples of semantic expressions:

1. Constructing a unit test for a specific function.
2. Computing the value of a mathematical expression.
3. Answering the factual question, e.g., “What is the birth date of George Washington?”
4. Generating a report based on a set of data.

## Select

### semantipy.select(s: [Semantics](#semantipy.Semantics) | str, return_type: type[SemanticTypeA]) → SemanticTypeA

### semantipy.select(s: [Semantics](#semantipy.Semantics) | str, selector: [Semantics](#semantipy.Semantics) | str) → [Semantics](#semantipy.Semantics)

### semantipy.select(s: [Semantics](#semantipy.Semantics) | str, selector: [Semantics](#semantipy.Semantics) | str, return_type: type[SemanticTypeA]) → SemanticTypeA

Selects elements from the given input based on the provided selector or return type.

The selector can be a semantic object or a string that specifies the criteria for selection.
Alternatively, a return type can be provided to indicate the type of elements to be selected.
If both a selector and a return type are provided, the function will use the selector to find
the elements and then return them in the specified return type.

## Select Iter

### semantipy.select_iter(s: [Semantics](#semantipy.Semantics) | str, selector: [Semantics](#semantipy.Semantics) | str) → Iterable[[Semantics](#semantipy.Semantics)]

### semantipy.select_iter(s: [Semantics](#semantipy.Semantics) | str, selector: [Semantics](#semantipy.Semantics) | str, return_type: type[SemanticTypeA]) → Iterable[SemanticTypeA]

Selects and iterates over elements based on a selector or return type.

Similar to select, but returns an iterable of elements instead of a single element.

## Split

### semantipy.split(s: [Semantics](#semantipy.Semantics) | str, selector: [Semantics](#semantipy.Semantics) | str) → Iterable[[Semantics](#semantipy.Semantics)]

### semantipy.split(s: [Semantics](#semantipy.Semantics) | str, selector: [Semantics](#semantipy.Semantics) | str, return_type: type[SemanticTypeA]) → Iterable[SemanticTypeA]

Split the input into multiple elements based on the provided selector or return type.

This function is similar to select_iter, but the selector is used to match the cutted parts rather than the chosen parts.

# LM Backend

### semantipy.configure_lm(lm: BaseChatModel) → None

An approach to configure the language model globally.

# Semantic Data

## Semantics

<a id="semantipy-semantics"></a>

### *class* semantipy.Semantics

## Text

<a id="semantipy-text"></a>

### *class* semantipy.Text(text: str)

Semantics that are represented with a pure textual string.

## Semantic Model

<a id="semantipy-semanticmodel"></a>

### *class* semantipy.SemanticModel

Semantics that are inherit a Pydantic model.

#### model_computed_fields *: ClassVar[Dict[str, ComputedFieldInfo]]* *= {}*

A dictionary of computed field names and their corresponding ComputedFieldInfo objects.

#### model_config *: ClassVar[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### model_fields *: ClassVar[Dict[str, FieldInfo]]* *= {}*

Metadata about the fields defined on the model,
mapping of field names to [FieldInfo][pydantic.fields.FieldInfo] objects.

This replaces Model._\_fields_\_ from Pydantic V1.

## Exemplar

<a id="semantipy-exemplar"></a>

### *class* semantipy.Exemplar(\*, input: [Text](#semantipy.Text) | [Semantics](#semantipy.Semantics), output: [Text](#semantipy.Text) | [Semantics](#semantipy.Semantics))

An example input-output pair.

#### model_computed_fields *: ClassVar[Dict[str, ComputedFieldInfo]]* *= {}*

A dictionary of computed field names and their corresponding ComputedFieldInfo objects.

#### model_config *: ClassVar[ConfigDict]* *= {'arbitrary_types_allowed': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### model_fields *: ClassVar[Dict[str, FieldInfo]]* *= {'input': FieldInfo(annotation=Union[Text, Semantics], required=True), 'output': FieldInfo(annotation=Union[Text, Semantics], required=True)}*

Metadata about the fields defined on the model,
mapping of field names to [FieldInfo][pydantic.fields.FieldInfo] objects.

This replaces Model._\_fields_\_ from Pydantic V1.

## Semantic List

### *class* semantipy.SemanticList(iterable=(), /)

Semantics that are represented with a list.

## Semantic Dict

### *class* semantipy.SemanticDict

Semantics that are represented with a dictionary.
