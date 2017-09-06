#!/usr/bin/perl

use strict;
use warnings;
use utf8;

use XML::LibXML;

if (scalar(@ARGV) < 5) {
    print STDERR "./efind.pl <TRED DIR> <ENTITIES DICTIONARY> <PML-TQ APP> <RESULTS DIR> <PML FILES DIR>\n";
    exit 1;
}

my $TRED_DIR = shift(@ARGV);
my $ENTITIES_DICT = shift(@ARGV);
my $PMLTQ_DIR = shift(@ARGV);
my $RESULTS = shift(@ARGV);

binmode(STDERR, ":encoding(utf8)");

## Nacitam entity
my $XML = XML::LibXML->load_xml(location => $ENTITIES_DICT);
my %entities = ();
my @entities = $XML->findnodes("//entity");

my $counter = 0;
foreach my $file (@ARGV) {
    my $prefix = $file;
    $prefix =~ s/^(?:.*\/)?([^\/]+)$/$1/;
    $prefix =~ s/(?:.*\/)?(\d{4}-\d{3}).*/$1/;

    if ($file !~ /.a$/) {
        next;
    }

    $counter++;
    print STDERR "\n\n******\n\t$file ($prefix) ($counter / " . scalar(@ARGV) . " )\n********\n\n";

    my $second_counter = 0;
    foreach my $entity (@entities) {
        $second_counter++;

        print STDERR "\n$second_counter\t";

        my $id = $entity->findnodes('./@id')->to_literal() . "";
        my $pml = $entity->findnodes('./pml_tq')->to_literal() . "";

        my $pml_for_print = $pml;        
        $pml_for_print =~ s/\n/ /g;
        print STDERR "$id\n\t$pml_for_print\t";

        if (-r "$RESULTS/$prefix-$id.txt") {
            print STDERR "\tResult exists.";
            next;
        }

        if (!$pml) {
            print STDERR "\tNo PML TQ\n";
            next;
        }

        my @lines = split(/\n/, $pml);
        if (scalar(split(/\$n/, $lines[0])) != scalar(split(/\$n/, $lines[1]))) {
            print STDERR "\t0: " . scalar(split(/\$n/, $lines[0])) . "\t";
            print STDERR "\t1: " . scalar(split(/\$n/, $lines[1])) . "\t";
            print STDERR "\tNo correct PML TQ\n";
            next;
        }

        print STDERR "\n\tStarting querying\n";

        ## Ulozim si dotaz do suboru
        open(PMLTQ_FILE, ">/tmp/dotaz");
        binmode(PMLTQ_FILE, ":encoding(utf8)");
        print PMLTQ_FILE $pml;
        close(PMLTQ_FILE);

        print STDERR system('echo $PERL5LIB');

        # my $perl_command = 'source /net/work/projects/perlbrew/init; eval "$(bash-complete setup)"; export PERL5LIB=""; perlbrew switch perl-5.22.1; export PERL5LIB="$HOME/treex/lib:$PERL5LIB"; which perl';
        my $pmltq_command = "$PMLTQ_DIR/pmltq --btred --query-file /tmp/dotaz $file > $RESULTS/$prefix-$id.txt";
        print STDERR "Command 2 : $pmltq_command\n";
        my $output = system($pmltq_command);
        print STDERR "Vysledok  : $output\n";

        ## Naslo daco?
        my $pocet_riadkov_vo_vysledku = `wc -l $RESULTS/$prefix-$id.txt`;
        $pocet_riadkov_vo_vysledku =~ s/(\n|\r)?//g;
        $pocet_riadkov_vo_vysledku =~ s/^\s*(\d+)\s.*/$1/;
        print STDERR "\tPocet vysledkov = $pocet_riadkov_vo_vysledku\n";

    }
}
