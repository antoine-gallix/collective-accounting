import click

main = click.Group()


@main.command
def do_this():
    pass


if __name__ == "__main__":
    # call the main group
    main()
