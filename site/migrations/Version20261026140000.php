<?php

declare(strict_types=1);

namespace DoctrineMigrations;

use Doctrine\DBAL\Schema\Schema;
use Doctrine\Migrations\AbstractMigration;

final class Version20261026140000 extends AbstractMigration
{
    public function getDescription(): string
    {
        return 'Add sample_count to benchmark and sample_index to result for independent model generations (model variance) alongside judge repeats';
    }

    public function up(Schema $schema): void
    {
        $this->addSql('ALTER TABLE benchmark ADD sample_count INT NOT NULL DEFAULT 1');
        $this->addSql('ALTER TABLE result ADD sample_index INT NOT NULL DEFAULT 1');
    }

    public function down(Schema $schema): void
    {
        $this->addSql('ALTER TABLE benchmark DROP sample_count');
        $this->addSql('ALTER TABLE result DROP sample_index');
    }
}