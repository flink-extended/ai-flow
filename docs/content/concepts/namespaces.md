# Namespaces

Namespaces provide a mechanism for isolating groups of [Workflows](./workflows.md) within a single cluster. Names of Workflows need to be unique within a namespace, but not across Namespaces.
Multiple business-related Workflows can be put into the same Namespace to have the same access control and Event isolation.


## Creating Namespaces

AIFlow has a default namespace called `default`. Users can also create their own namespaces if needed through the command-line interface.

```shell script
aiflow namespace add user_namespace
```

## Viewing Namespaces

```shell script
aiflow namespace list
```

## Deleting Namespaces

```shell script
aiflow namespace delete user_namespace
```