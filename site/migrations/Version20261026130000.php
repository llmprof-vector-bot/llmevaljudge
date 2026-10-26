<?php

declare(strict_types=1);

namespace DoctrineMigrations;

use Doctrine\DBAL\Schema\Schema;
use Doctrine\Migrations\AbstractMigration;

/**
 * Optional per-model reasoning effort (OpenAI-style reasoning_effort).
 *
 * NULL = the parameter is not sent at all (safe for providers/models that do
 * not support or validate the field). Values follow the provider's vocabulary:
 * none|low|medium|high — validated by the target chain (some providers reject
 * unsupported values, others silently ignore them).
 */
final class Version20261026130000 extends AbstractMigration
{
    public function getDescription(): string
    {
        return 'Add nullable model.reasoning_effort column (OpenAI-style reasoning_effort; omitted from requests when NULL)';
    }

    public function up(Schema $schema): void
    {
        $this->addSql('ALTER TABLE model ADD reasoning_effort VARCHAR(16) DEFAULT NULL');
    }

    public function down(Schema $schema): void
    {
        $this->addSql('ALTER TABLE model DROP reasoning_effort');
    }
}