#!/usr/bin/sh
#

echo "This script will install NSAT on your machine!"
echo "Do you want to proceed [Y/n]?"
read answer

if [ "$answer" == "n" ]; then
    echo "You missed the oportunity to install something great on your machine!"
else
    declare -a target_dirs=("lib" "data")

    echo ""
    echo "Create all the necessary directories!"
    for i in "${target_dirs[@]}"
    do
        mkdir -p $i
    done
    echo "Directories created!"
    echo ""
    echo "Install pyNCSre!"
    pip install --upgrrade pyNCSre --user
    pip2 install --upgrade pyNCSre --user
    echo "puNCSre has been installed!"

    echo ""
    echo "Install pyNSAT library!"
    python setup.py develop --user
    python2 setup.py develop --user
    echo "pyNSATlib is now installed!"

    exp_cmd="export "
    target_lib="$LD_LIBRARY_PATH:`pwd`/lib"
    exp_=$exp_cmd$target_lib
    bashrc=~/.bashrc
    if [ ! -f $bashrc ]
    then
        echo $0: File '${bashrc}' not found!
        echo "I create one ..."
        touch $bashrc
    fi

    nlines=$(wc -l < "$bashrc")
    sed -i "$nlines a $exp_" ~/.bashrc

    echo ""
    echo "Compiling NSAT library!"
    make cleanall; make 
    echo "NSAT has been compiled!"

    echo ""
    echo "Now you can use NSAT!"
    echo "Example:  python tests/pythons/test_reset.py"
fi